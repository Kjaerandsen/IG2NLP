from utility.componentStatistics import *

def test_removeSuffixes() -> None:

   text = removeSuffixes("A1(1) A1,p1(2), Cex(3), Bdir1,p(4), Bdir,p1(5)")

   assert text == "A(1) A,p(2), Cex(3), Bdir,p(4), Bdir,p(5)"

   text = "A1(1) A1,p2(2) A,p3(3) I5(5) Bdir6(6) Bdir7,p(7) Bdir,p8(8) Cex9(9)" + \
      "Bind1(1) Bind1,p1(2) Cac3(3) E1,p1(4) E1(5) P1(6) P1,p1(7)"
   
   text = removeSuffixes(text)

   assert text == "A(1) A,p(2) A,p(3) I(5) Bdir(6) Bdir,p(7) Bdir,p(8) Cex(9)" + \
      "Bind(1) Bind,p(2) Cac(3) E,p(4) E(5) P(6) P,p(7)"

   assert removeSuffixes("A(1) A,p(2), Cex(3), Bdir,p(4), Bdir,p(5)") == \
      "A(1) A,p(2), Cex(3), Bdir,p(4), Bdir,p(5)"
   
def test_removeAnnotations() -> None:
   assert removeAnnotations("A(1) A,p(2), Cex(3), Bdir,p(4), Bdir,p(5) Cex{6 A(Attribute)}") == \
      "1 2, 3, 4, 5 6 attribute"
   
   assert \
      removeAnnotations("A[semanticAnnotation](1) A,p(2), Cex(3), \
Bdir,p(4), Bdir,p(5) Cex{6 A(Attribute)}") \
         == "1 2, 3, 4, 5 6 attribute"
   
   assert \
      removeAnnotations("Bdir(something) A[semanticAnnotation](1) A,p(2), Cex(3), \
Bdir,p(4), Bdir,p(5) Cex{6 A(Attribute)}") \
         == "something 1 2, 3, 4, 5 6 attribute"

   assert removeAnnotations("Cac{A, Cac{A(B) I([C]) D Bdir[semantic](E)}, \
F Bdir{A(G) H I([I]) or the I(J)}}") == \
   "a b c d e f g h i j"
   
def test_removeNesting() -> None:

   assert removeNesting("Cex{6 A(Attribute)}") == "Cex{6 attribute}"

   assert removeNesting("Cac{1 Cex{2}} A(3)") == "Cac{1 2} A(3)"

   assert removeNesting("Cac{A, Cac{A(B) I([C]) D Bdir[semantic](E)}, F Bdir{A(G) H I([I]) or the \
I(J)}}") == "Cac{a b c d e f g h i j}"