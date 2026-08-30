"""Read me first — Anzeige mit Kapitel-Navigation.

User 29.08.: „waer super, wenn das, was angezeigt wird, auch hin- und
herklickbar ist, dass wir mit Ueberschriften arbeiten koennten oder Kapiteln."
Deshalb links die Kapitelliste, rechts der Text; ein Klick springt, ohne die
Seite neu zu laden. Die Reihenfolge und die Textschluessel stehen in
core.readmefirst, hier steht nur die Darstellung.
"""
import html
import json

from core.readmefirst import KONTAKT, kapitel
from core.sprache import t


def render(als_overlay=False):
    """-> Seiten-INHALT. als_overlay=True legt denselben Inhalt ueber die
    laufende Seite (der Fall beim ersten Zugriff nach einem Neustart);
    sonst ist es eine gewoehnliche Seite hinter dem Knopf."""
    ks = kapitel(t)
    nav = "".join(
        f'<a href="#rm-{html.escape(k["anker"])}" data-rm="{html.escape(k["anker"])}"'
        f'{" class=aktiv" if i == 0 else ""}>{html.escape(k["titel"])}</a>'
        for i, k in enumerate(ks))
    absaetze = "".join(
        f'<section id="rm-{html.escape(k["anker"])}">'
        f'<h2>{html.escape(k["titel"])}</h2>'
        + "".join(f"<p>{html.escape(z)}</p>"
                  for z in str(k["text"]).split("\n\n") if z.strip())
        + "</section>"
        for k in ks)
    schliessen = (f'<button class="gtb on" id="rm-zu">'
                  f'{html.escape(t("readme.schliessen"))}</button>'
                  if als_overlay else
                  # User 30.08.: "kam ich nicht mehr raus. Ein Escape funktionierte
                  # nicht. Und ein Knopf, das zu schliessen, war auch nicht da."
                  # Die Vollseite HAT die Navigation, aber keinen Weg zurueck an der
                  # Stelle, an der man ihn sucht — oben rechts, wo im Overlay das
                  # Schliessen sitzt. Hier fuehrt er zurueck, woher man kam, sonst
                  # auf die Startseite.
                  f'<a class="gtb on" id="rm-zurueck" href="/heute">'
                  f'{html.escape(t("readme.zurueck"))}</a>')
    js = (
        '<script>(function(){'
        # .374: die klebende Kopfleiste ist je nach Umbruch, Sprache und
        # Unterreiterzeile verschieden hoch — gemessen 30.08. 77,3 px ohne und
        # 114,1 px mit zweiter Ebene. Deshalb wird sie GEMESSEN und als
        # --kopf-h gefuehrt; Sprungziele (scroll-margin-top) und die klebende
        # Kapitelliste (top) rechnen im CSS damit. Ein Festwert im CSS war
        # genau der Fehler, den der Kommentar ueber .kopf schon einmal
        # beschreibt (das alte top:41px der zweiten Navigationsebene).
        'var kopf=document.querySelector(".kopf");'
        'var kh=function(){return kopf?kopf.getBoundingClientRect().height:0;};'
        'var setzh=function(){'
        'document.documentElement.style.setProperty("--kopf-h",kh()+"px");};'
        'setzh();'
        'if(kopf&&window.ResizeObserver)new ResizeObserver(setzh).observe(kopf);'
        'else window.addEventListener("resize",setzh);'
        # Kapitel-Wechsel ohne Seitenwechsel: Klick markiert und scrollt.
        'var n=document.querySelectorAll(".rm-nav a");'
        'n.forEach(function(a){a.onclick=function(e){e.preventDefault();'
        'n.forEach(function(x){x.classList.remove("aktiv")});a.classList.add("aktiv");'
        'var z=document.getElementById("rm-"+a.dataset.rm);'
        'if(z)z.scrollIntoView({behavior:"smooth",block:"start"});};});'
        # Beim Scrollen wandert die Markierung mit — sonst zeigt die Liste
        # nach zwei Handgriffen etwas anderes an als der sichtbare Text.
        # .374: der Zuhoerer hing fest an .rm-text. Das scrollt aber NUR im
        # Overlay in sich (max-height + overflow-y); auf der Vollseite ist es
        # ein gewoehnlicher Flex-Block, gescrollt wird das Dokument — und
        # dessen scroll-Ereignis steigt nicht zu einem Kind ab. Der Handler
        # feuerte dort nie, die Liste blieb auf dem ersten Kapitel stehen.
        # Jetzt wird der naechste WIRKLICH scrollende Vorfahr gesucht (im
        # Overlay .rm-text bzw. auf dem Handy .rm-overlay), sonst das Fenster.
        'var t_=document.querySelector(".rm-text");var sc=window;'
        'for(var e_=t_;e_&&e_!==document.body;e_=e_.parentElement){'
        'var ov=getComputedStyle(e_).overflowY;'
        'if((ov==="auto"||ov==="scroll")&&e_.scrollHeight>e_.clientHeight){'
        'sc=e_;break;}}'
        'if(t_)sc.addEventListener("scroll",function(){'
        # Bezugskante: beim Fenster die Unterkante der klebenden Leiste
        # (darueber ist nichts sichtbar), sonst die Oberkante des Scrollers.
        'var b=(sc===window?kh():sc.getBoundingClientRect().top)+40,akt=null;'
        't_.querySelectorAll("section").forEach(function(s){'
        'if(s.getBoundingClientRect().top<=b)akt=s.id.slice(3);});'
        'if(akt)n.forEach(function(x){'
        'x.classList.toggle("aktiv",x.dataset.rm===akt);});},{passive:true});'
        # Schliessen setzt die Marke auf dem SERVER (nicht im Browser):
        # der Zustand gehoert zur Installation, s. core/readmefirst.py.
        'var z=document.getElementById("rm-zu");'
        'var zb=z||document.getElementById("rm-zurueck");'
        # Escape schliesst das Overlay UND verlaesst die Vollseite — auf beiden
        # Wegen der Griff, den jeder zuerst probiert.
        'if(zb)document.addEventListener("keydown",function(e){'
        'if(e.key==="Escape")zb.click();});'
        'if(z)z.onclick=function(){z.disabled=true;'
        'fetch("/readme_gesehen",{method:"POST"}).then(function(){'
        'var o=document.getElementById("rm-overlay");if(o)o.remove();'
        '}).catch(function(){z.disabled=false;});};'
        '})();</script>')
    kern = (f'<div class="rm-kopf"><h1>{html.escape(t("readme.titel"))}</h1>'
            f'{schliessen}</div>'
            f'<p class="rm-einl">{html.escape(t("readme.einleitung"))}</p>'
            f'<div class="rm-huelle">'
            f'<nav class="rm-nav"><div class="rm-navtitel">'
            f'{html.escape(t("readme.inhalt"))}</div>{nav}</nav>'
            f'<div class="rm-text">{absaetze}'
            + (f'<p class="rm-kontakt">{html.escape(t("readme.kontakt"))} '
               f'<a href="mailto:{html.escape(KONTAKT)}">{html.escape(KONTAKT)}</a></p>'
               if KONTAKT else '')
            + (f'<p class="rm-fuss">{html.escape(t("readme.fuss"))}</p>'
               if als_overlay else '')
            + '</div></div>')
    if als_overlay:
        return (f'<div class="rm-overlay" id="rm-overlay"><div class="rm-karte">'
                f'{kern}</div></div>{js}')
    return f'<div class="rm-seite">{kern}</div>{js}'
