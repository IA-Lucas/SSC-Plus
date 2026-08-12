"""Timeout operacional encerra o CLI npm inteiro, nao apenas o pai."""

import ctypes
import os
import sys
import tempfile
import time
import unittest

import apoio  # noqa: F401

_RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
for _rel in ("05_p0", "08_p2"):
    _caminho = os.path.join(_RAIZ, _rel)
    if _caminho not in sys.path:
        sys.path.insert(0, _caminho)

from preflight.adaptadores import sensor_subprocess as sensor_preflight  # noqa: E402
from provedor_assinatura import (RC_TIMEOUT,  # noqa: E402
                                 sensor_subprocess as sensor_p2)


def processo_vivo(pid: int) -> bool:
    if os.name != "nt":
        try:
            os.kill(pid, 0)
            return True
        except ProcessLookupError:
            return False
    acesso = 0x1000  # PROCESS_QUERY_LIMITED_INFORMATION
    handle = ctypes.windll.kernel32.OpenProcess(acesso, False, pid)
    if not handle:
        return False
    try:
        codigo = ctypes.c_ulong()
        if not ctypes.windll.kernel32.GetExitCodeProcess(
                handle, ctypes.byref(codigo)):
            return False
        return codigo.value == 259  # STILL_ACTIVE
    finally:
        ctypes.windll.kernel32.CloseHandle(handle)


class TimeoutMataAArvore(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="arvore-timeout-")
        self.addCleanup(self.tmp.cleanup)

    def comando_com_neto(self):
        pid_file = os.path.join(self.tmp.name, "neto.pid")
        filho = ("import os,time;"
                 f"open({pid_file!r},'w').write(str(os.getpid()));"
                 "time.sleep(30)")
        pai = ("import subprocess,sys,time;"
               f"subprocess.Popen([sys.executable,'-c',{filho!r}]);"
               "time.sleep(30)")
        return [sys.executable, "-c", pai], pid_file

    def exigir_neto_morto(self, pid_file):
        self.assertTrue(os.path.exists(pid_file),
                        "o neto nao chegou a existir; o caso nao foi exercido")
        with open(pid_file, encoding="ascii") as arquivo:
            pid = int(arquivo.read())
        for _ in range(20):
            if not processo_vivo(pid):
                break
            time.sleep(0.05)
        self.assertFalse(processo_vivo(pid),
                         f"processo neto {pid} sobreviveu ao timeout")

    def test_preflight_mata_o_neto(self):
        comando, pid_file = self.comando_com_neto()
        rc, _, _ = sensor_preflight(comando, env={}, timeout=1)
        self.assertEqual(rc, 124)
        self.exigir_neto_morto(pid_file)

    def test_p2_mata_o_neto(self):
        comando, pid_file = self.comando_com_neto()
        rc, _, _ = sensor_p2(comando, env={}, timeout=1,
                             cwd=self.tmp.name)
        self.assertEqual(rc, RC_TIMEOUT)
        self.exigir_neto_morto(pid_file)


if __name__ == "__main__":
    unittest.main()
