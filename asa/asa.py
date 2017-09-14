# -*- coding: utf-8 -*-
import os
import re
from subprocess import Popen, PIPE

re_wakati = re.compile('^\d+\t')
re_column = re.compile('^([a-z]+): (.+)')
ASA_VERSION = '20170503'


class ASA(object):
    def __init__(self, path, encoding='utf8'):
        self.jar = os.path.join(path, 'ASA%s.jar' % ASA_VERSION)
        os.chdir(path)
        self.encoding = encoding

    def _parse_asa_return(self, asa_return):
        results = []
        for line in asa_return.splitlines()[4:-1]:
            line = line.strip()
            if line.startswith('ID: '):
                results.append(dict())
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
        command = 'echo %s | java -cp %s cl.asa.Asa 2>/dev/null' % (sentence, self.jar)
        proc = Popen(command, shell=True, stdin=PIPE, stdout=PIPE)
        asa_return = proc.communicate()[0].decode(self.encoding)
        return self._parse_asa_return(asa_return)
