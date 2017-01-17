from pyspark import SparkContext
from pyspark.streaming import StreamingContext
from pyspark.streaming.kafka import KafkaUtils
from ctapipe.image.cleaning import tailcuts_clean
from ctapipe.io import CameraGeometry
from ctapipe.image.hillas import hillas_parameters, HillasParameterizationError
from astropy import units as u

import msgpack
import msgpack_numpy as m
from ctapipe.reco.FitGammaHillas import FitGammaHillas
from ctapipe.io.hessio import hessio_event_source

# we read the instrument configuration from an arbitrary simtel file
# instrument info does not change per event. (except for pointing maybe)
source = hessio_event_source('gamma_test.simtel.gz', max_events=7)
instrument = next(source).inst

# Create a local StreamingContext with three working threads and batch
# interval of 5 seconds
sc = SparkContext('local[3]', 'test app')
broadcastInst = sc.broadcast(instrument)
ssc = StreamingContext(sc, 5)


def reco(single_telescope_data):
    fit = FitGammaHillas()
    inst = broadcastInst.value
    hillas_dict, tel_phi, tel_theta = single_telescope_data

    fit_result = fit.predict(hillas_dict, inst, tel_phi, tel_theta)
    return fit_result


def hillas(event):
    hillas_dict = {}
    tel_phi = {}
    tel_theta = {}
    for tel in event:
        tel_id = tel['tel_id']
        tel_phi[tel_id] = 0.*u.deg
        tel_theta[tel_id] = 20.*u.deg

        pmt_signal = tel['adc_sums'][0]
        # print(pmt_signal)
        inst = broadcastInst.value
        pix_x = inst.pixel_pos[tel_id][0]
        pix_y = inst.pixel_pos[tel_id][1]
        foc = inst.optical_foclen[tel_id]
        cam_geom = CameraGeometry.guess(pix_x, pix_y, foc)
        mask = tailcuts_clean(cam_geom, pmt_signal, 1,
                              picture_thresh=10., boundary_thresh=5.)
        pmt_signal[mask == 0] = 0

        try:
            moments = hillas_parameters(cam_geom.pix_x,
                                        cam_geom.pix_y,
                                        pmt_signal)
            hillas_dict[tel['tel_id']] = moments
        except HillasParameterizationError as e:
            print(e)

    return (hillas_dict, tel_phi, tel_theta)


def decoder(d):
    d = msgpack.unpackb(d, encoding='utf8', object_hook=m.decode)
    return d


zkQuorum = 'localhost:2181'
dataStream = KafkaUtils.createStream(ssc=ssc,
                                     zkQuorum=zkQuorum,
                                     groupId='rta_group',
                                     topics={'data': 1},
                                     valueDecoder=decoder,
                                     kafkaParams={
                                      'metadata.broker.list': 'localhost:9092',
                                      'fetch.message.max.bytes': '104857600',
                                      })


sums = dataStream.mapValues(hillas)\
                 .filter(lambda t: len(t[1][0]) > 2)\
                 .mapValues(reco)\
                 .count()
sums.pprint()

ssc.start()
ssc.awaitTerminationOrTimeout(timeout=600)
