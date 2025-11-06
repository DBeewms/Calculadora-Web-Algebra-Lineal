import unittest

from algebra.logic import metodos


class TestBiseccion(unittest.TestCase):

    def test_convergencia_normal(self):
        # f(x) = x^3 - x - 1 tiene una raíz entre 1 y 2
        res = metodos.biseccion('x**3 - x - 1', 1, 2, tol=1e-8, maxit=200)
        self.assertTrue(res.get('convergio'))
        # f_en_raiz debe ser cercano a 0
        froot = res.get('f_en_raiz')
        self.assertIsNotNone(froot)
        self.assertAlmostEqual(float(froot), 0.0, places=6)

    def test_raiz_en_extremo(self):
        # f(x) = x tiene raíz exactamente en a=0
        res = metodos.biseccion('x', 0, 1, tol=1e-8, maxit=50)
        self.assertTrue(res.get('convergio'))
        self.assertEqual(float(res.get('raiz')), 0.0)

    def test_sin_cambio_de_signo(self):
        # f(x) = x^2 + 1 no tiene raíz real; debe lanzar ErrorBiseccion
        with self.assertRaises(metodos.ErrorBiseccion):
            metodos.biseccion('x**2 + 1', 0, 1)

    def test_potencia_usuario_caret(self):
        # Algunos usuarios escriben x^10 en lugar de x**10. Probar ambas formas.
        res1 = metodos.biseccion('x**10 - 1', 0.5, 2, tol=1e-8, maxit=200)
        self.assertTrue(res1.get('convergio'))
        res2 = metodos.biseccion('x^10 - 1', 0.5, 2, tol=1e-8, maxit=200)
        self.assertTrue(res2.get('convergio'))


if __name__ == '__main__':
    unittest.main()
