"""
Executor de Testes — ENER-GUARDIAN
Descobre e executa todos os testes da pasta tests/ utilizando a biblioteca padrão unittest.
"""
import unittest
import sys

if __name__ == "__main__":
    print("Iniciando a execução dos testes do ENER-GUARDIAN...")
    loader = unittest.TestLoader()
    suite = loader.discover("tests")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(not result.wasSuccessful())
