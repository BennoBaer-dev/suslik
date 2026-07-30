"""Wurzel-Anker (M0, Modul-Konzept §4 FALLE 0): ALLE Pfade beziehen sich auf die
Projekt-Wurzel — nie auf dirname(__file__) des jeweiligen Moduls. Grund: nach einer
Modul-Verschiebung zeigt __file__ ins Unterverzeichnis; der execv-Neustart haette
das falsche Modul gestartet, und KEIN Gate faengt execv. Deshalb definiert DIESES
Modul den Anker genau einmal; core/ liegt EINE Ebene unter der Wurzel."""
import os

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERIFYD_PFAD = os.path.join(WURZEL, "verifyd.py")
