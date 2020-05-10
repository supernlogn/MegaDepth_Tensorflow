import tensorflow as tf
import numpy as np


class ConstantWeightsInitializer(object):
    def __init__(self, weightsDictionary):
        """ Initialize weights in the Hourglass model
        Arguments:
            weightsDictionary {dictionary} -- dictionary of numpy arrays holding the weights of each
        """
        self.weightsDictionary = weightsDictionary
            
    def conv2d_kernel(self, path, index=0):
        if index > 0:
            conv2dChoice = 'conv2d_{}/kernel'.format(index)
        else:
            conv2dChoice = 'conv2d/kernel'
        return tf.constant_initializer(self.weightsDictionary[path + conv2dChoice])            
    
    def conv2d_bias(self, path, index=0):
        if index > 0:
            conv2dChoice = 'conv2d_{}/bias'.format(index)
        else:
            conv2dChoice = 'conv2d/bias'
        return tf.constant_initializer(self.weightsDictionary[path +conv2dChoice])
    
    def BN_mean(self, path, index=0):
        if index > 0:
            bnChoice = 'batch_normalization_{}/moving_mean'.format(index)
        else:
            bnChoice = 'batch_normalization/moving_mean'
        return tf.constant_initializer(self.weightsDictionary[path + bnChoice])
    
    def BN_variance(self, path, index=0):
        if index > 0:
            bnChoice = 'batch_normalization_{}/moving_variance'.format(index)
        else:
            bnChoice = 'batch_normalization/moving_variance' 
        return tf.constant_initializer(self.weightsDictionary[path + bnChoice])
    
    def BN_gamma(self, path, index=0):
        if index > 0:
            bnChoice = 'batch_normalization_{}/gamma'.format(index)
        else:
            bnChoice = 'batch_normalization/gamma'
        return tf.constant_initializer(self.weightsDictionary[path + bnChoice])
    
    def BN_beta(self, path, index=0):
        if index > 0:
            bnChoice = 'batch_normalization_{}/beta'.format(index)
        else:
            bnChoice = 'batch_normalization/beta'
        return tf.constant_initializer(self.weightsDictionary[path + bnChoice])


class Inception_Base(tf.keras.Model):
    def __init__(self,config, index, initializer=None, path=''):
        super(Inception_Base,self).__init__()
        filt = config[0]
        out_a = config[1]
        out_b = config[2]
        if initializer:
            self.conv1 = tf.keras.layers.Conv2D(out_a,1,1, 
                                            kernel_initializer=initializer.conv2d_kernel(path, index),
                                            bias_initializer=initializer.conv2d_bias(path, index))
            self.bn1 = tf.keras.layers.BatchNormalization(center=False,scale=False,
                                                      moving_mean_initializer=initializer.BN_mean(path, index),
                                                      moving_variance_initializer=initializer.BN_variance(path, index))

            self.conv2 = tf.keras.layers.Conv2D(out_b,filt,1,padding='same',
                                            kernel_initializer=initializer.conv2d_kernel(path, index+1),
                                            bias_initializer=initializer.conv2d_bias(path, index+1))
            self.bn2 = tf.keras.layers.BatchNormalization(center=False,scale=False,
                                                    moving_mean_initializer=initializer.BN_mean(path, index+1),
                                                    moving_variance_initializer=initializer.BN_variance(path, index+1))
        else:
            self.conv1 = tf.keras.layers.Conv2D(out_a,1,1)
            self.bn1 = tf.keras.layers.BatchNormalization(center=False,scale=False)

            self.conv2 = tf.keras.layers.Conv2D(out_b,filt,1,padding='same')
            self.bn2 = tf.keras.layers.BatchNormalization(center=False,scale=False)

    def call(self, x):
        x = self.conv1(x)
        x = self.bn1(x)
        x = tf.nn.relu(x)

        x = self.conv2(x)
        x = self.bn2(x)
        x = tf.nn.relu(x)
        return x




class Inception(tf.keras.Model):
    def __init__(self,config, initializer=None, path=''):
        super(Inception,self).__init__()
        stride = 1
        out_layers = config[0][0]
        kernel_size = 1
        
        if initializer:
            self.conv0 = tf.keras.layers.Conv2D(out_layers,1,1,
                                                kernel_initializer=initializer.conv2d_kernel(path),
                                                bias_initializer=initializer.conv2d_bias(path))
            self.bn0 = tf.keras.layers.BatchNormalization(center=False, scale=False,
                                                          moving_mean_initializer=initializer.BN_mean(path),
                                                          moving_variance_initializer=initializer.BN_variance(path))
        else:
            self.conv0 = tf.keras.layers.Conv2D(out_layers,1,1)
            self.bn0 = tf.keras.layers.BatchNormalization(center=False, scale=False)

        self.inception_1 = Inception_Base(config[1], 1, initializer=initializer, path=path)
        self.inception_2 = Inception_Base(config[2], 3, initializer=initializer, path=path)
        self.inception_3 = Inception_Base(config[3], 5, initializer=initializer, path=path)

    def call(self, x):
        out0 = self.conv0(x)
        out0 = self.bn0(out0)
        out0 = tf.nn.relu(out0)

        out1 = self.inception_1(x)
        out2 = self.inception_2(x)
        out3 = self.inception_3(x)

        out = tf.concat([out0,out1,out2,out3],3)

        return out

class Channel1(tf.keras.Model):
    def __init__(self, initializer=None, path=''):
        super(Channel1,self).__init__()
        
        path0 = path + '0/0/' # 3/0/0/3/0/0/3/0/0/3/0/0/
        self.inception0_0 = Inception([[64], [3, 32, 64], [5, 32, 64], [7, 32, 64]], initializer, path=path0+'0/')
        self.inception0_1 = Inception([[64], [3, 32, 64], [5, 32, 64], [7, 32, 64]], initializer, path=path0+'1/')

        
        
        self.pool = tf.keras.layers.AveragePooling2D(2, 2)
        path1 = path + '0/1/'
        self.inception1_0 = Inception([[64], [3, 32, 64], [5, 32, 64], [7, 32, 64]], initializer, path=path1+ '1/')
        self.inception1_1 = Inception([[64], [3, 32, 64], [5, 32, 64], [7, 32, 64]], initializer, path=path1+ '2/')
        self.inception1_2 = Inception([[64], [3, 32, 64], [5, 32, 64], [7, 32, 64]], initializer, path=path1+ '3/')
        self.upsample = tf.keras.layers.UpSampling2D((2,2), interpolation='bilinear')
        
    def call(self,x):
        with tf.name_scope('0/0'):
            with tf.name_scope('0'):
                out0 = self.inception0_0(x)
            with tf.name_scope('1'):
                out0 = self.inception0_1(out0)
                
        with tf.name_scope('0/1'):
            with tf.name_scope('0'):
                pool = self.pool(x)
            with tf.name_scope('1'):
                out1 = self.inception1_0(pool)
            with tf.name_scope('2'):
                out1 = self.inception1_1(out1)
            with tf.name_scope('3'):
                out1 = self.inception1_2(out1)
            with tf.name_scope('4'):
                out1 =  self.upsample(out1)

        out = out0 + out1

        return out

class Channel2(tf.keras.Model):
    def __init__(self, initializer=None, path=''):
        super(Channel2,self).__init__()

        path0 = path +'0/0/' # 3/0/0/3/0/0/3/0/0/
        self.inception0_0 = Inception([[64], [3, 32, 64], [5, 32, 64], [7, 32, 64]], initializer, path=path0+'0/')
        self.inception0_1 = Inception([[64], [3, 64, 64], [7, 64, 64], [11, 64, 64]], initializer, path=path0+'1/')

        self.pool = tf.keras.layers.AveragePooling2D(2, 2)

        path1 = path +'0/1/'
        self.inception1_0 = Inception([[64], [3, 32, 64], [5, 32, 64], [7, 32, 64]], initializer, path=path1+'1/')
        self.inception1_1 = Inception([[64], [3, 32, 64], [5, 32, 64], [7, 32, 64]], initializer, path=path1+'2/')
        self.channel = Channel1(initializer, path=path1+'3/')
        self.inception1_2 = Inception([[64], [3, 32, 64], [5, 32, 64], [7, 32, 64]], initializer, path=path1+'4/')
        self.inception1_3 = Inception([[64], [3, 64, 64], [7, 64, 64], [11, 64, 64]], initializer, path=path1+'5/')
        self.upsample = tf.keras.layers.UpSampling2D((2,2), interpolation='bilinear')

    def call(self, x):
        with tf.name_scope('0/0'):
            with tf.name_scope('0'):
                out0 = self.inception0_0(x)
            with tf.name_scope('1'):
                out0 = self.inception0_1(out0)

        with tf.name_scope('0/1'):
            with tf.name_scope('0'):
                pool = self.pool(x)
            with tf.name_scope('1'):
                out1 = self.inception1_0(pool)
            with tf.name_scope('2'):
                out1 = self.inception1_1(out1)
            with tf.name_scope('3'):
                out1 = self.channel(out1)
            with tf.name_scope('4'):
                out1 = self.inception1_2(out1)
            with tf.name_scope('5'):
                out1 = self.inception1_3(out1)
            with tf.name_scope('6'):
                out1 = self.upsample(out1)

        out = out1 + out0
        return out


class Channel3(tf.keras.Model):
    def __init__(self, initializer=None, path=''):
        super(Channel3,self).__init__()

        self.pool = tf.keras.layers.MaxPool2D(2, 2)
        
        path0 = path +'0/0/' # 3/0/0/3/0/0/
        self.inception0_0 = Inception([[32], [3, 32, 32], [5, 32, 32], [7, 32, 32]], initializer, path=path0+'1/')
        self.inception0_1 = Inception([[64], [3, 32, 64], [5, 32, 64], [7, 32, 64]], initializer, path=path0+'2/')
        self.channel = Channel2(initializer,path=path0+'3/')
        self.inception0_2 = Inception([[64], [3, 32, 64], [5, 32, 64], [7, 32, 64]], initializer, path=path0+'4/')
        self.inception0_3 = Inception([[32], [3, 32, 32], [5, 32, 32], [7, 32, 32]], initializer, path=path0+'5/')

        path1 = path +'0/1/'
        self.inception1_0 = Inception([[32], [3, 32, 32], [5, 32, 32], [7, 32, 32]], initializer, path=path1+'0/')
        self.inception1_1 = Inception([[32], [3, 64, 32], [7, 64, 32], [11, 64, 32]], initializer, path=path1+'1/')
        self.upsample = tf.keras.layers.UpSampling2D((2,2), interpolation='bilinear')

    def call(self, x):
        with tf.name_scope('0/0'):
            with tf.name_scope('0'):
                pool = self.pool(x)
            with tf.name_scope('1'):
                out1 = self.inception0_0(pool)
            with tf.name_scope('2'):
                out1 = self.inception0_1(out1)
            with tf.name_scope('3'):
                out1 = self.channel(out1)
            with tf.name_scope('4'):
                out1 = self.inception0_2(out1)
            with tf.name_scope('5'):
                out1 = self.inception0_3(out1)
            with tf.name_scope('6'):
                out1 = self.upsample(out1)
        
        with tf.name_scope('0/1'):
            with tf.name_scope('0'):
                out0 = self.inception1_0(x)
            with tf.name_scope('1'):
                out0 = self.inception1_1(out0)
        
        out = out1 + out0
        return out

class Channel4(tf.keras.Model):
    def __init__(self, initializer=None, path=''):
        super(Channel4,self).__init__()

        self.pool = tf.keras.layers.MaxPool2D(2, 2)
        
        path0 = path + '0/0/'# 3/0/0/
        self.inception0_0 = Inception([[32], [3, 32, 32], [5, 32, 32], [7, 32, 32]], initializer, path=path0+'1/')
        self.inception0_1 = Inception([[32], [3, 32, 32], [5, 32, 32], [7, 32, 32]], initializer, path=path0+'2/')
        self.channel = Channel3(initializer, path=path0+'3/')
        self.inception0_2 = Inception([[32], [3, 64, 32], [5, 64, 32], [7, 64, 32]], initializer, path=path0+'4/')
        self.inception0_3 = Inception([[16], [3, 32, 16], [7, 32, 16], [11, 32, 16]], initializer, path=path0+'5/')

        path1= path + '0/1/'
        self.inception1_0 = Inception([[16], [3, 64, 16], [7, 64, 16], [11, 64, 16]], initializer, path=path1+'0/')
        #self.inception1_1 = Inception([[32], [3, 64, 32], [7, 64, 32], [11, 64, 32]])
        self.upsample = tf.keras.layers.UpSampling2D((2,2), interpolation='bilinear')
    
    def call(self, x):
        with tf.name_scope('0/0'):
            with tf.name_scope('0'):
                pool = self.pool(x)
            with tf.name_scope('1'):
                out1 = self.inception0_0(pool)
            with tf.name_scope('2'):
                out1 = self.inception0_1(out1)
            with tf.name_scope('3'):
                out1 = self.channel(out1)
            with tf.name_scope('4'):
                out1 = self.inception0_2(out1)
            with tf.name_scope('5'):
                out1 = self.inception0_3(out1)
            with tf.name_scope('6'):
                out1 = self.upsample(out1)

        with tf.name_scope('0/1'):
            with tf.name_scope('0'):
                out0 = self.inception1_0(x)
        #out0 = self.inception1_1(out0)
        out = out1 + out0
        return out

class Hourglass(tf.keras.Model):
    def __init__(self, weightsPath=None, training=True, normalize=False, path=''):
        super(Hourglass,self).__init__()
        out_layers_1a = 128
        kernel_size_1a = 7
        stride_1a = 1
        out_layers_3a = 1
        kernel_size_3a = 3
        stride_3a = 1
        self.normalize = normalize
        self.training = training
    
        if(weightsPath):
            weightsDictionary = np.load(weightsPath, allow_pickle=True)[()]
            initializer = ConstantWeightsInitializer(weightsDictionary)
        else:
            initializer = None

        # with path+'conv2d' as varPath:
        if initializer:
            path0 = path + '0/'
            self.conv0 = tf.keras.layers.Conv2D(out_layers_1a,kernel_size_1a,stride_1a,padding='same', activation=None,
                                                kernel_initializer=initializer.conv2d_kernel(path0),
                                                bias_initializer=initializer.conv2d_bias(path0))
            
            path1 = path + '1/'
            self.bn0 = tf.keras.layers.BatchNormalization(beta_initializer=initializer.BN_beta(path1), 
                                                        gamma_initializer=initializer.BN_gamma(path1),
                                                        moving_mean_initializer=initializer.BN_mean(path1),
                                                        moving_variance_initializer=initializer.BN_variance(path1))
        else:
            self.conv0 = tf.keras.layers.Conv2D(out_layers_1a,kernel_size_1a,stride_1a,padding='same')
            self.bn0 = tf.keras.layers.BatchNormalization()

        self.channel = Channel4(initializer, path= path + '3/')
        if initializer:
            conv1path = path + '4/'
            self.conv1 = tf.keras.layers.Conv2D(out_layers_3a,kernel_size_3a,stride_3a,padding='same', activation=None,
                                                kernel_initializer=initializer.conv2d_kernel(conv1path),
                                                bias_initializer=initializer.conv2d_bias(conv1path))
        else:
            self.conv1 = tf.keras.layers.Conv2D(out_layers_3a,kernel_size_3a,stride_3a,padding='same')


    def call(self,x):
        # pre-processing
        if self.normalize == True:
            x = tf.math.scalar_mul(1.0/255,x)
        # fridaymodel
        with tf.name_scope('module'):
            with tf.name_scope('0'):
               out = self.conv0(x)
            with tf.name_scope('1'):
                out = self.bn0(out)
            with tf.name_scope('2'):
               out = tf.nn.relu(out)
            with tf.name_scope('3'):
                out = self.channel(out)
            with tf.name_scope('4'):
                out = self.conv1(out)

            #post-processing
            out = tf.squeeze(out) # (1, 384, 512, 1)
            out = tf.math.exp(out)
            pred_inv_depth = tf.math.divide(1.0, out)
            pred_inv_depth = tf.math.divide(pred_inv_depth, tf.reduce_max(pred_inv_depth))
            

        return pred_inv_depth