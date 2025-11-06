import unittest
import math

from algebra.logic import metodos


class TestBiseccionExtra(unittest.TestCase):

    def test_trig_sin(self):
        # f(x) = sin(x) - 0.5 tiene una raíz en pi/6 (~0.523598)
        res = metodos.biseccion('sin(x) - 0.5', 0, 2, tol=1e-10, maxit=200)
        self.assertTrue(res.get('convergio'))
        raiz = float(res.get('raiz'))
        self.assertAlmostEqual(raiz, math.pi / 6, places=6)

    def test_log(self):
        # f(x) = log(x) - 1 tiene raíz en e (~2.71828)
        res = metodos.biseccion('log(x) - 1', 2, 4, tol=1e-10, maxit=200)
        self.assertTrue(res.get('convergio'))
        raiz = float(res.get('raiz'))
        self.assertAlmostEqual(raiz, math.e, places=6)

    def test_exp(self):
        # f(x) = exp(x) - 20 tiene raíz en ln(20)
        res = metodos.biseccion('exp(x) - 20', 2, 4, tol=1e-10, maxit=200)
        self.assertTrue(res.get('convergio'))
        raiz = float(res.get('raiz'))
        self.assertAlmostEqual(raiz, math.log(20), places=6)

    def test_sqrt(self):
        # f(x) = sqrt(x) - 2 tiene raíz en 4
        res = metodos.biseccion('sqrt(x) - 2', 0, 10, tol=1e-10, maxit=200)
        self.assertTrue(res.get('convergio'))
        raiz = float(res.get('raiz'))
        self.assertAlmostEqual(raiz, 4.0, places=6)

    def test_invalid_expr_raises(self):
        # Expresión inválida debe levantar ErrorBiseccion
        with self.assertRaises(metodos.ErrorBiseccion):
            metodos.biseccion('sin(', 0, 1)

    def test_max_iterations_no_converge(self):
        # Con maxit muy pequeño el método no alcanza la tolerancia
        res = metodos.biseccion('x - 0.1', 0, 1, tol=1e-12, maxit=1)
        self.assertFalse(res.get('convergio'))
        self.assertEqual(res.get('conteo_iter'), 1)


if __name__ == '__main__':
    unittest.main()
