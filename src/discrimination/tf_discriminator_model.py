import sys, os  

sys.path.append(os.getcwd())
from config import *

import tensorflow as tf
import numpy as np
import random, time

tf.logging.set_verbosity(tf.logging.ERROR)

class Attention_Discriminator:
  def __init__(self, sess):
    # Initialize with setting
    self.sess = sess

  # def load(self, model_url):
    # self.saver = tf.train.import_meta_graph(model_url)
    # self.saver.restore(self.sess, tf.train.latest_checkpoint('./'))
    # self.sess.run(tf.global_variables_initializer())

  def build_model(self):
    # Set initial vars
    self.x = tf.placeholder(tf.float32, [BATCH_S, MAX_SEQUENCE_LENGTH, N_FEATURES], name="horizontal")
    self.y = tf.placeholder(tf.float32, [BATCH_S, MAX_SEQUENCE_LENGTH, N_FEATURES], name="vertical")
    self.target = tf.placeholder(tf.float32, [BATCH_S, 2], name="target")  

    # Encode x
    with tf.variable_scope("encode_x"):
      self.fwd_lstm = tf.nn.rnn_cell.BasicLSTMCell(N_HIDDEN, state_is_tuple=True)
      self.x_output, self.x_state = tf.nn.dynamic_rnn(cell=self.fwd_lstm, inputs=self.x, dtype=tf.float32)

    # Encode y
    with tf.variable_scope("encode_y"):
      self.fwd_lstm = tf.nn.rnn_cell.BasicLSTMCell(N_HIDDEN, state_is_tuple=True)
      self.y_output, self.y_state = tf.nn.dynamic_rnn(cell=self.fwd_lstm, inputs=self.y, initial_state=self.x_state, dtype=tf.float32)

    # Get Y
    self.Y = self.x_output  

    ### Build W^y
    self.W_Y = tf.get_variable("W_Y", shape=[N_HIDDEN, N_HIDDEN])
    unshaped_M_left = tf.matmul(tf.reshape(self.Y, shape=[BATCH_S * MAX_SEQUENCE_LENGTH, N_HIDDEN]), self.W_Y, name="M_left")
    self.M_left = tf.reshape(unshaped_M_left, shape=[BATCH_S, MAX_SEQUENCE_LENGTH, N_HIDDEN])
    ################

    ### Get h_n repeated
    y_transposed = tf.transpose(self.y_output, [1, 0, 2])
    self.h_n = tf.gather(y_transposed, int(y_transposed.get_shape()[0]) - 1)
    self.h_n_e = tf.expand_dims(self.h_n, 1)
    e_l = tf.pack([1, MAX_SEQUENCE_LENGTH, 1])
    self.h_n_e = tf.tile(self.h_n_e, e_l)
    ################

    ### Build W^h
    self.W_h = tf.get_variable("W_h", shape=[N_HIDDEN, N_HIDDEN])
    unshaped_M_right = tf.matmul(tf.reshape(self.h_n_e, shape=[BATCH_S * MAX_SEQUENCE_LENGTH, N_HIDDEN]), self.W_h)
    self.M_right = tf.reshape(unshaped_M_right, shape=[BATCH_S, MAX_SEQUENCE_LENGTH, N_HIDDEN], name="M_right")
    #################

    #### The beautiful beautiful attention mechanism ####
    self.M = tf.tanh(tf.add(self.M_left, self.M_right), name="M")
    self.W_att = tf.get_variable("W_att",shape=[N_HIDDEN,1]) 

    alpha = tf.matmul(tf.reshape(self.M, shape=[BATCH_S * MAX_SEQUENCE_LENGTH, N_HIDDEN]), self.W_att)
    self.att = tf.nn.softmax(tf.reshape(alpha, shape=[BATCH_S, 1, MAX_SEQUENCE_LENGTH], name="att")) 

    self.r = tf.reshape(tf.batch_matmul(self.att, self.Y, name="r"),shape=[BATCH_S, N_HIDDEN])
    ####################################################

    ### Build W_p (b_p is bias)
    self.W_p, self.b_p= tf.get_variable("W_p", shape=[N_HIDDEN, N_HIDDEN]), tf.get_variable("b_p",shape=[N_HIDDEN],initializer=tf.constant_initializer())
    self.Wpr = tf.matmul(self.r, self.W_p, name="Wy") + self.b_p
    ###################

    ### Build W_x
    self.W_x, self.b_x = tf.get_variable("W_x", shape=[N_HIDDEN, N_HIDDEN]), tf.get_variable("b_x",shape=[N_HIDDEN],initializer=tf.constant_initializer())
    self.Wxhn = tf.matmul(self.h_n, self.W_x, name="Wxhn") + self.b_x
    ###################

    ### Reached the end :)
    self.hstar = tf.tanh(tf.add(self.Wpr, self.Wxhn), name="hstar")
    self.W_pred = tf.get_variable("W_pred", shape=[N_HIDDEN, 2])
    self.pred = tf.nn.softmax(tf.matmul(self.hstar, self.W_pred), name="pred_layer")
    ###################

    ### Loss function
    self.loss = -tf.reduce_sum(self.target * tf.log(self.pred), name="loss")
    ###################

    # Number of correct, not normalized
    correct = tf.equal(tf.argmax(self.pred,1),tf.argmax(self.target,1))
    # Number of correct, not normalized
    correct = tf.equal(tf.argmax(self.pred,1),tf.argmax(self.target,1))
    # Accuracy
    self.acc = tf.reduce_mean(tf.cast(correct, "float"), name="accuracy")

    # Setting optimizers
    self.optimizer = tf.train.AdamOptimizer()
    self.optim = self.optimizer.minimize(self.loss, var_list=tf.trainable_variables())

    __ = tf.scalar_summary("loss", self.loss)

  def train(self, training_data, testing_data, len_training, len_testing, iterations):

    # Initializing tf + timing
    merged_sum = tf.merge_all_summaries()
    tf.initialize_all_variables().run()
    # self.saver = tf.train.Saver()
    
    print(training_data['x'])
    print(training_data['targets'])

    for j in range(iterations):
      print("\n################\nIteration: ", j)
      start_time = time.time()
    
      # Run through training data
      for i in range(0, len_training, BATCH_S):
        feed_dict = {
                self.x: np.array(training_data['x'][i:i + BATCH_S]), 
                self.y: np.array(training_data['y'][i:i + BATCH_S]), 
                self.target: np.array(training_data['targets'][i:i + BATCH_S])
            }
        att, __ , train_loss, train_acc, summ = self.sess.run([self.att,  self.optim, self.loss, self.acc, merged_sum], feed_dict = feed_dict)
        print("Train loss: ", train_loss, "\nTrain acc on train: ", train_acc)

      # Run through testing data
      total_testing_acc=[]
      for i in range(0, len_testing, BATCH_S):
        feed_dict = {
                self.x: testing_data['x'][i:i + BATCH_S], 
                self.y: testing_data['y'][i:i + BATCH_S], 
                self.target: testing_data['targets'][i:i + BATCH_S]
            }
        att, __, testing_loss, testing_acc, summ = self.sess.run([self.att, self.optim, self.loss, self.acc, merged_sum], feed_dict = feed_dict)
        total_testing_acc.append(testing_acc)
      print("Testing acc on test: ", np.mean(total_testing_acc))

      elapsed_time = time.time() - start_time
      print("Iteration took: ", elapsed_time)

    # self.saver.save(self.sess, PROJ_ROOT+"models/tf_discrim")