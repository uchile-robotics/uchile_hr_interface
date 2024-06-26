#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-


import rospy
from std_msgs.msg import String
import smach
import smach_ros

# Definir el estado que publica en el tópico speech
class SpeechState(smach.State):
    def __init__(self, speech_text):
        smach.State.__init__(self, outcomes=['succeeded'])
        self.speech_text = speech_text

    def execute(self, userdata):
        rospy.loginfo('Publicando en el tópico /say: %s', self.speech_text)
        pub = rospy.Publisher('/say', String, queue_size=10)
        rospy.sleep(1)  # Esperar un momento para asegurarse de que el nodo está conectado
        pub.publish(self.speech_text)
        return 'succeeded'


class HearState(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes=['heared', 'timeout'], output_keys=['heared_data'])
        self.subscriber = None
        self.detected_speech = None

    def execute(self, userdata):
        rospy.loginfo('Esperando mensaje en el tópico /recognized_speech...')
        self.detected_speech = None
        self.subscriber = rospy.Subscriber('/recognized_speech', String, self.callback)

        # Esperar hasta que se reciba un mensaje o hasta que pase el timeout (10 segundos en este caso)
        timeout = rospy.Time.now() + rospy.Duration(10)
        while not rospy.is_shutdown() and self.detected_speech is None and rospy.Time.now() < timeout:
            rospy.sleep(0.1)

        self.subscriber.unregister()

        if self.detected_speech is not None:
            userdata.heared_data = self.detected_speech
            rospy.loginfo(self.detected_speech)
            return 'heared'
        else:
            return 'timeout'

    def callback(self, msg):
        self.detected_speech = msg.data

def main():
    rospy.init_node('smach_speech_node')

    # Crear una máquina de estado SMACH
    sm = smach.StateMachine(outcomes=['succeeded', 'timeout'])

    # Añadir estados a la máquina de estado
    with sm:
        smach.StateMachine.add('HEAR', HearState(), transitions={'heared':'SPEECH', 'timeout':'HEAR'}, remapping={'heared_data':'heared_data'})
        smach.StateMachine.add('SPEECH', SpeechState('Hola, este es un mensaje de prueba'), transitions={'succeeded':'succeeded'})

    # Ejecutar la máquina de estado
    outcome = sm.execute()

if __name__ == '__main__':
    main()
