from scipy.io import wavfile
import scipy.signal
import os
#Print the current directory
print(os.getcwd())

new_fs = 88200
# open data
sample_rate, data = wavfile.read('classes/audio-manip/output_pyaudio.wav')

# resample data
new_num_samples = round(len(data)*float(new_fs)/sample_rate)
data = scipy.signal.resample(data, new_num_samples)
wavfile.write(filename="new_fs_output_scipy.wav", rate=88200, data=data)