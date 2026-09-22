% Hechos y regla de ejemplo
padre(juan, ana).
padre(juan, pedro).
edad(juan, 52).
nombre_completo(ana, "Ana Perez").
etiqueta('persona adulta').

abuelo(X, Z) :-
    padre(X, Y),
    padre(Y, Z).

calculo(Resultado) :- Resultado is 2 ** 3 + 10 mod 4.
lista([Cabeza|Cola]) :- \+ Cola == [], !.
?- abuelo(juan, Quien).
