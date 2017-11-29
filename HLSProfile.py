from random import randint, random as rand, choice
from base64 import standard_b64encode as b64
import string
inf = ['#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=',',CLOSED-CAPTIONS="cc",FRAME-RATE=29.97,CODECS="avc1.4d001f,mp4a.40.2",AUDIO="mp4a.40.2_63K",RESOLUTION=']
class HLSProfile:
    def __init__(self, profile_key, failure_probability):
        self.faxscm = None
        self.sequence_start = -1
        self.sequence_count = -1
        self.template = None
        self.target_duration = -1
        self.profile_key = profile_key
        self.number_of_profiles = -1
        self.failure_probability = failure_probability

    def setFaxs(self, faxscm):
        self.faxscm = faxscm

    def setTargetDuration(self, target_duration):
        self.target_duration = target_duration

    def setTemplate(self, template):
        self.template = template

    def setSequenceStart(self, sequence_start):
        self.sequence_start = sequence_start

    def setSequenceCount(self, sequence_count):
        self.sequence_count = sequence_count

    def setNumberOfProfiles(self, number_of_profiles):
        self.number_of_profiles = number_of_profiles

    def generateMaster(self):
        if (self.template == None):
            raise Exception("No template provided for hls generator")
        if (not isinstance(self.template, list)):
            self.template = self.template.split("\n")

        output = []
        index = 0
        while index < len(self.template):
            line = self.template[index].strip()
            if "${base-64}" in line:
                line = line.replace("${base-64}", str(self.faxscm))
                output.append(line)
            elif "${create-profile}" in line:
                self.create_profiles(output)
            else:
                output.append(line)
            index = index + 1

        return '\n'.join(output)

    def generateNumberArgument(self, original, lower_bound, upper_bound):
        return (original if rand() > self.failure_probability else randint(lower_bound, upper_bound))

    def generateBase64Argument(self, original):
        random_b64 = ''.join(choice(string.ascii_uppercase + string.digits) for _ in range(15))
        return (original if rand() > self.failure_probability else b64(random_b64))

    def logRandom(self, origin, generated, source):
        if origin != generated:
            print self.profile_key,"Generated random value:",source

    def generateProfile(self):
        if (self.template == None):
            raise Exception("No template provided for hls generator")
        if (self.sequence_count == -1 or self.sequence_start == -1):
            raise Exception("No sequence count or sequence start set")
        if (self.target_duration == -1):
            raise Exception("No target duration set")

        if (not isinstance(self.template, list)):
            self.template = self.template.split("\n")

        output = []
        index = 0
        starting_sequence = self.sequence_start
        while index < len(self.template):
            line = self.template[index].strip()
            if "${target-duration}" in line:
                value = self.generateNumberArgument(self.target_duration, 1, 10)
                line = line.replace("${target-duration}", str(value))
                self.logRandom(self.target_duration, value, "TARGET DURATION")
                output.append(line)
            elif "${media-sequence}" in line:
                starting_sequence = self.generateNumberArgument(self.sequence_start, self.sequence_start - self.sequence_count, self.sequence_start + self.sequence_count)
                line = line.replace("${media-sequence}", str(starting_sequence))
                self.logRandom(self.sequence_start, starting_sequence, "MEDIA SEQUENCE")
                output.append(line)
            elif "${base-64}" in line:
                value = self.generateBase64Argument(self.faxscm)
                line = line.replace("${base-64}", str(value))
                self.logRandom(self.sequence_start, value, "FAXS-CM")
                output.append(line)
            elif "${create-segment}" in line:
                num_created = self.create_segments(output, starting_sequence)
                self.sequence_start = self.sequence_start + self.sequence_count
            else:
                output.append(line)
            index = index + 1

        return '\n'.join(output)

    def create_segments(self, output, starting_sequence_base):
        segments = []
        sequence_count = self.generateNumberArgument(self.sequence_count, 1, 15)
        starting_sequence = self.generateNumberArgument(starting_sequence_base, starting_sequence_base - 2, starting_sequence_base + 2)
        self.logRandom(self.sequence_count, sequence_count, "NUMBER OF SEGMENTS GENERATED")
        self.logRandom(starting_sequence_base, starting_sequence, "MEDIA SEQUENCE STARTING POINT")
        for i in range(self.sequence_count):
            target_dur = self.generateNumberArgument(self.target_duration, 1, 10)
            segments.append("#EXTINF:" + str(target_dur) + "," + str(starting_sequence + i))
            segments.append(self.profile_key + str(starting_sequence + i))
            self.logRandom(self.target_duration, target_dur, "SEGMENT TARGET DURATION #" + str(i))
        output.extend(segments)
        return len(segments) / 2

    def create_profiles(self, output):
        segments = []
        bandwidths = []
        heights = []
        widths = []
        for i in range(self.number_of_profiles):
            bandwidths.append(randint(1, 1000000))
            heights.append(randint(1, 4000))
            widths.append(randint(1, 4000))

        bandwidths.sort()
        heights.sort()
        widths.sort()
        for i in range(self.number_of_profiles):
            segments.append(inf[0] + str(bandwidths[i]) + inf[1] + str(heights[i]) + "," + str(widths[i]))
            segments.append("profiles/0" + str(i + 1) + ".m3u8")
        output.extend(segments)
