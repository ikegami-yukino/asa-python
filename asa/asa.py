import os
import re
from subprocess import Popen, PIPE
import tempfile
import time

ASA_VERSION = '20170503'

re_id = re.compile('ID: (\d+)')
re_wakati = re.compile('^\d+\t')
re_column = re.compile('^([a-z]+): (.+)')


class ASA(object):
    """Argument Structure Analyzer (ASA)
    It requires ASA2017503.jar available at following URL:
    http://www.cl.cs.okayama-u.ac.jp/wp-content/uploads/2017/05/asa20170503.tgz

    >>> import asa
    >>> analyzer = asa.ASA('path-to-the-ASA-directory')
    >>> analyzer.parse('彼は村長だ')
    [{'ID': 0,
      'category': '人',
      'frame': '1-copula',
      'link': 1,
      'main': '彼',
      'part': 'は',
      'tense': 'PRESENT',
      'type': 'elem',
      'wakati': ['彼\tカレ\t彼\t名詞,代名詞,一般\t\t\tO', 'は\tハ\tは\t助詞,係助詞\t\t\tO']},
     {'ID': 1,
      'category': '人',
      'frame': '0-elem',
      'link': -1,
      'main': '村長',
      'mood': 'INDICATIVE',
      'part': 'だ',
      'polarity': 'AFFIRMATIVE',
      'sentelem': 'PREDICATE',
      'tense': 'PRESENT',
      'type': 'copula',
      'voice': 'ACTIVE',
      'wakati': ['村長\tソンチョウ\t村長\t名詞,一般\t\t\tO', 'だ\tダ\tだ\t助動詞\t特殊・ダ\t基本形\tO']}]
    """

    def __init__(self, asa_dir, loading_wait=1, encoding='utf-8'):
        """
        Params:
            asa_dir (str) : directory path of ASA's jar
            loading_wait (float) : time of initial loading (default 1.0)
            encoding (str) : character encoding (default utf-8)
        """
        self.jar = os.path.join(asa_dir, 'ASA%s.jar' % ASA_VERSION)
        os.chdir(asa_dir)
        self.encoding = encoding
        self.tempfile = tempfile.mkstemp()[1]
        command = 'java -cp %s cl.asa.Asa > %s' % (self.jar, self.tempfile)
        self.asa = Popen(command, shell=True, stdin=PIPE, stdout=PIPE)
        time.sleep(loading_wait)

    def __del__(self):
        os.remove(self.tempfile)

    def _parse_asa_return(self, asa_return):
        results = []
        for line in asa_return.splitlines():
            if line.startswith(('起動中', 'input', 'sentence')):
                continue
            elif 'MB: ' in line:
                continue
            line = line.strip()
            if line.startswith('ID: '):
                id_ = int(re_id.search(line).group(1))
                results.append({'ID': id_})
            elif re_wakati.search(line):
                wakatis = results[-1].get('wakati', [])
                wakatis.append(re_wakati.sub('', line))
                results[-1]['wakati'] = wakatis
            else:
                for (key, value) in re_column.findall(line):
                    if value.isdigit() or value == '-1':
                        value = int(value)
                    results[-1][key] = value
        return results

    def parse(self, sentence):
        """Parse the sentence
        Param:
            sentence (str)
        Return:
            result (list of dict)
        """
        self.asa.stdin.write(sentence.encode(self.encoding) + b'\n')
        self.asa.stdin.flush()
        result = []
        while not result:
            with open(self.tempfile, 'r', encoding=self.encoding) as out:
                asa_return = out.read()
            if asa_return and asa_return.splitlines()[-1].startswith('input'):
                result = self._parse_asa_return(asa_return)
            time.sleep(0.1)
        open(self.tempfile, 'w').close()  # Initialize temp file
        return result
