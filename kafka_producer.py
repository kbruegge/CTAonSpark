# from kafka import KafkaProducer
from pykafka import KafkaClient


# from ctapipe.io.hessio import hessio_event_source
from itertools import cycle
import time
from ctapipe.io.hessio import hessio_event_source
import copy
# import numpy as  np
import threading
import logging

import msgpack
import msgpack_numpy as m
m.patch()
#
source = hessio_event_source('gamma_test.simtel.gz', max_events=7)
events = list(copy.deepcopy(e) for e in source)

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(levelname)s] (%(threadName)-10s) %(message)s',
)


def create_serialized_slow_data(event):
    data = []
    for tel_id, t in event.dl0.tel.items():
        pix_x = event.inst.pixel_pos[tel_id][0].value
        pix_y = event.inst.pixel_pos[tel_id][1].value
        focal_length = event.inst.optical_foclen[tel_id].value
        tel_x = event.inst.tel_pos[tel_id].value
        tel_y = event.inst.tel_pos[tel_id].value

        d = {'tel_id': tel_id,
             'pix_x': pix_x,
             'pix_y': pix_y,
             'focal_length': focal_length,
             'tel_pos_x': tel_x,
             'tel_pos_y': tel_y
             }
        data.append(d)
    return msgpack.packb(data)


def create_serialized_data(event):
    data = []
    for tel_id, t in event.dl0.tel.items():
        d = {'adc_sums': t.adc_sums,
             'tel_id': tel_id,
             }
        data.append(d)

    return msgpack.packb(data)


def send_data(data_topic):
    data_producer = data_topic.get_producer(max_request_size=3000036)
    i = 0
    for event in cycle(events):
        # time.sleep(0.5)  # sleep a second
        i += 1
        data = create_serialized_data(event)
        event_id = event.dl0.event_id
        if i % 1000 == 0:
            logging.debug('Sending Data')
        data_producer.produce(data, partition_key='{}'.format(event_id).encode())

#
# def send_slow_data(data_topic):
#     data_producer = data_topic.get_producer(max_request_size=3000036)
#     for event in cycle(events):
#         time.sleep(4)  # sleep 4 seconds
#         data = create_serialized_slow_data(event)
#         event_id = event.dl0.event_id
#         logging.debug('Sending Data')
#         data_producer.produce(data, partition_key='{}'.format(event_id).encode())


def main():
    client = KafkaClient(hosts='localhost:9092')
    data_topic = client.topics['data'.encode()]
    # slow_topic = client.topics['slow'.encode()]
    # producer = KafkaProducer(bootstrap_servers='localhost:9092',
    #                          key_serializer=str.encode,
    #                          value_serializer=teh_pickle
    #                          )
    t = threading.Thread(target=send_data, args=(data_topic,), name='data')
    t.start()
    # t2 = threading.Thread(target=send_slow_data, args=(slow_topic,), name='slow')
    # t2.start()


if __name__ == '__main__':
    main()
