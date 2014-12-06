import random
from bitarray import bitarray
from math import ceil, log
from hashlib import sha512
import time
import logging

logger = logging.getLogger('bloomfilter')


class Bloomfilter:
    def __init__(self, bitsize, desired_elements):
        if bitsize < 2:
            raise ValueError("too small")
        self.m = bitsize
        self.k = int(ceil((float(bitsize) / float(desired_elements)) * log(2)))
        self.array = bitarray(bitsize)
        self.array.setall(False)
        logger.debug("Set up Bloomfilter, m={}, k={}".format(self.m, self.k))

    def _element_to_bits_multi_seed(self, element):
        def sample_one_bit_pos(seed, max_val):
            random.seed(seed)
            bit_position = random.randint(0, max_val)
            return bit_position

        bits = []
        stepsize = len(element) / self.k
        if stepsize == 0:
            raise Exception("Can't support a k this high")

        slices = []
        for i in xrange(self.k):
            a_slice = element[i * stepsize:(i + 1) * stepsize]
            slices.append(a_slice)

        for a_slice in slices:
            bit = sample_one_bit_pos(int(a_slice, 16), self.m - 1)
            bits.append(bit)
        return bits

    def _element_to_bits_one_seed(self, element):
        random.seed(element)
        bits = random.sample(xrange(self.m), self.k)
        return bits

    def _element_to_bits_one_seed_no_xrange(self, element):
        random.seed(element)
        bits = [random.randint(0, self.m - 1) for _ in xrange(self.k)]
        return bits

    def element_to_bits(self, element):
        return self._element_to_bits_one_seed(element)

    def add(self, element):
        for b in self.element_to_bits(element):
            self.array[b] = True

    def is_present(self, element):
        for b in self.element_to_bits(element):
            if not self.array[b]:
                return False
        return True

    def snapshot(self):
        return self.array.copy()


def sxor(s1, s2):
    # convert strings to a list of character pair tuples
    # go through each tuple, converting them to ASCII code (ord)
    # perform exclusive or on the ASCII code
    # then convert the result back to ASCII (chr)
    # merge the resulting array of characters as a string
    return ''.join(chr(ord(a) ^ ord(b)) for a, b in zip(s1, s2))


if __name__ == "__main__":

    def number_to_hash(num):
        return sha512(str(num)).hexdigest()

    def test_bloom_filter():
        bitsize = 16000000
        desired = 2000000

        actual = desired  # 100000

        snapshot_delta = desired / 8
        number_of_false_positive_tests = 10000

        false_neg = 0
        false_pos = 0

        t_start = time.time()
        print "Bloomfilter test m=%d, n=%d" % (bitsize, actual)
        bf = Bloomfilter(bitsize, desired)

        print bf.element_to_bits(number_to_hash(1))
        print bf.element_to_bits(number_to_hash(2))

        print "running..."

        for i in xrange(actual - snapshot_delta):
            bf.add(number_to_hash(i))
            if not bf.is_present(number_to_hash(i)):
                false_neg += 1

        for i in xrange(actual - snapshot_delta, actual):
            bf.add(number_to_hash(i))
            if not bf.is_present(number_to_hash(i)):
                false_neg += 1

        print "filled"
        for i in xrange(actual, number_of_false_positive_tests + actual):
            if bf.is_present(number_to_hash(i)):
                false_pos += 1

        t_end = time.time()
        print "False negatives: %d" % false_neg
        print "False positives: %d, rate %.3f percent" % (
            false_pos, 100.0 * float(false_pos) / float(number_of_false_positive_tests))
        print "Time: %d seconds" % (int(t_end - t_start))

    test_bloom_filter()