"""
pdf_generator.py -- Utilitaire de génération de fichiers PDF via HTML (Jinja2 + xhtml2pdf)
Fournit les fonctions pour générer les bulletins scolaires et les emplois du temps avec un style soigné.
"""

import io
from xhtml2pdf import pisa
from jinja2 import Environment, BaseLoader
import datetime

# =====================================================================
# TEMPLATES HTML avec CSS intégré (spécial xhtml2pdf)
# =====================================================================

BULLETIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Bulletin Scolaire</title>
    <style>
        @page {
            size: A4 portrait;
            margin: 1.5cm;
            @frame footer_frame {
                -pdf-frame-content: footer_content;
                left: 1.5cm; width: 18cm; top: 27cm; height: 2cm;
            }
        }
        body {
            font-family: Helvetica, sans-serif;
            font-size: 11pt;
            color: #2c3e50;
        }
        /* EN-TÊTE */
        .school-header {
            width: 100%;
            border-bottom: 3px solid #1565C0;
            padding-bottom: 10px;
            margin-bottom: 30px;
        }
        .school-title {
            color: #1565C0;
            font-size: 26pt;
            font-weight: bold;
            margin: 0;
            padding: 0;
        }
        .school-subtitle {
            font-size: 12pt;
            color: #7f8c8d;
            margin: 5px 0 0 0;
        }
        
        /* BANDEAU ELEVE */
        .student-info {
            width: 100%;
            background-color: #f8f9fa;
            border: 1px solid #e0e0e0;
            padding: 15px;
            margin-bottom: 25px;
            border-radius: 8px; /* unsupported by older xhtml2pdf, but safe */
        }
        .student-name {
            font-size: 18pt;
            font-weight: bold;
            color: #2c3e50;
        }
        .info-table { width: 100%; margin-top: 10px; }
        .info-table td { padding: 3px; }
        
        /* TABLEAU NOTES */
        table.grades {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }
        table.grades th {
            background-color: #1565C0;
            color: white;
            text-align: left;
            padding: 10px;
            font-size: 11pt;
            border: 1px solid #1565C0;
        }
        table.grades td {
            padding: 10px;
            border: 1px solid #bdc3c7;
            font-size: 11pt;
        }
        table.grades tr.even_row td { background-color: #f2f6fa; }
        
        .col-mat { width: 45%; }
        .col-coef { width: 15%; text-align: center; }
        .col-moy { width: 20%; text-align: center; font-weight: bold; }
        .col-pts { width: 20%; text-align: center; }

        .note-good { color: #27ae60; }
        .note-ok { color: #f39c12; }
        .note-bad { color: #c0392b; }

        /* ZONES RESULTATS */
        .results-box {
            width: 100%;
            margin-top: 20px;
            border: 1px solid #bdc3c7;
        }
        .results-box td {
            padding: 10px;
            border-bottom: 1px solid #bdc3c7;
        }
        table.results { width: 100%; border-collapse: collapse; }
        
        .total-brut { font-size: 12pt; color: #34495e; }
        .penalite { font-size: 12pt; color: #c0392b; font-weight:bold; }
        .total-net { font-size: 12pt; color: #2980b9; font-weight:bold; }
        
        .moyenne-finale {
            background-color: #1565C0;
            color: white;
            font-size: 18pt;
            font-weight: bold;
            text-align: center;
            padding: 15px;
            margin-top: 15px;
        }
        
        .footer-sig {
            width: 100%;
            margin-top: 50px;
        }
        .footer-sig td { text-align: center; padding-top: 10px; font-weight: bold; }
    </style>
</head>
<body>

    <!-- ENTÊTE ACADEMIX -->
    <table class="school-header">
        <tr>
            <td width="70%">
                <h1 class="school-title">ACADEMIX SCHOOL</h1>
                <p class="school-subtitle">Excellence, Rigueur & Discipline<br>Année Scolaire {{ annee }}</p>
            </td>
            <td width="30%" align="right" valign="top">
                <span style="font-size: 28pt; color: #1565C0;">🎓</span>
            </td>
        </tr>
    </table>

    <h2 style="text-align: center; margin-bottom: 20px; font-size: 16pt;">BULLETIN TRIMESTRIEL - TRIMESTRE {{ trimestre }}</h2>

    <!-- INFOS ÉLÈVE -->
    <div class="student-info">
        <div class="student-name">{{ eleve.nom }} {{ eleve.prenom }}</div>
        <table class="info-table">
            <tr>
                <td width="50%"><b>Matricule :</b> {{ "%s"|format(eleve.matricule) if eleve.matricule else "N/A" }}</td>
                <td width="50%" align="right"><b>Classe :</b> {{ classe_nom }}</td>
            </tr>
        </table>
    </div>

    <!-- NOTES MATIÈRES -->
    <table class="grades">
        <tr>
            <th class="col-mat">Matière</th>
            <th class="col-coef">Coeff.</th>
            <th class="col-moy">Moyenne (/20)</th>
            <th class="col-pts">Points</th>
        </tr>
        {% for ligne in lignes %}
        <tr class="{% if loop.index0 % 2 == 0 %}even_row{% else %}odd_row{% endif %}">
            <td>{{ ligne.nom }}</td>
            <td align="center">{{ ligne.coefficient }}</td>
            <td align="center">
                <span class="{% if ligne.moyenne|float >= 10 %}note-good{% elif ligne.moyenne|float >= 6 %}note-ok{% else %}note-bad{% endif %}">
                    {{ "%.2f"|format(ligne.moyenne|float) }}
                </span>
            </td>
            <td align="center">{{ "%.2f"|format(ligne.points|float) }} pts</td>
        </tr>
        {% else %}
        <tr>
            <td colspan="4" align="center"><i>Aucune note saisie pour ce trimestre.</i></td>
        </tr>
        {% endfor %}
    </table>

    {% if lignes %}
    <!-- SYNTHÈSE TRIMESTRE -->
    <div class="results-box">
        <table class="results">
            <tr>
                <td width="70%" class="total-brut">Total des points bruts (toutes matières confondues)</td>
                <td width="30%" align="right" class="total-brut"><b>{{ "%.2f"|format(total_pts_brut|float) }} pts</b></td>
            </tr>
            <tr>
                <td class="penalite">
                    Pénalité Disciplinaire d'Absences<br>
                    <span style="font-size:10pt; color:gray; font-weight:normal;">
                        ({{ "%.1f"|format(heures_nj|float) }}h Non Justifiées / {{ "%.1f"|format(heures_j|float) }}h Justifiées)
                    </span>
                </td>
                <td align="right" class="penalite">- {{ "%.2f"|format(penalite_pts|float) }} pts</td>
            </tr>
            <tr>
                <td class="total-net">Total des points Nets</td>
                <td align="right" class="total-net">{{ "%.2f"|format(total_pts_nets|float) }} pts</td>
            </tr>
        </table>
        
        <div class="moyenne-finale">
            MOYENNE TRIMESTRIELLE DÉFINITIVE : {{ "%.2f"|format(moy_definitive|float) }} / 20
        </div>
    </div>
    {% endif %}

    <table class="footer-sig">
        <tr>
            <td width="50%">Visa du Professeur Titulaire</td>
            <td width="50%">Le Directeur des Études</td>
        </tr>
    </table>

    <!-- FOOTER PAGE -->
    <div id="footer_content" style="text-align: center; color: #95a5a6; font-size: 9pt; border-top: 1px solid #e0e0e0; padding-top: 5px;">
        Academix School Management • Imprimé le {{ date_generation }} • Page <pdf:pagenumber>
    </div>

</body>
</html>
"""


TIMETABLE_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Emploi du Temps</title>
    <style>
        @page {
            size: A4 landscape;
            margin: 1cm;
            @frame footer_frame {
                -pdf-frame-content: footer_content;
                left: 1cm; width: 27.7cm; top: 19.5cm; height: 1.5cm;
            }
        }
        body { font-family: Helvetica, sans-serif; font-size: 10pt; color: #333; }
        
        .header { text-align: center; margin-bottom: 20px; }
        .header h1 { color: #1565C0; margin: 0; padding: 0; font-size: 24pt; font-weight: bold; }
        .header h2 { color: #555; margin: 5px 0 0 0; font-size: 14pt; }
        
        table.timetable {
            width: 100%;
            border-collapse: collapse;
            table-layout: fixed;
        }
        table.timetable th, table.timetable td {
            border: 1px solid #bdc3c7;
            padding: 5px;
            text-align: center;
            vertical-align: top;
        }
        table.timetable th {
            background-color: #1565C0;
            color: white;
            font-size: 12pt;
            height: 30px;
            vertical-align: middle;
        }
        .col-heure { width: 10%; background-color: #ecf0f1; font-weight: bold; color: #2c3e50; vertical-align: middle;}
        .col-jour { width: 15%; }
        
        .creneau {
            background-color: #e3f2fd;
            padding: 8px 5px;
            margin: 2px 0;
            border-bottom: 1px solid #90caf9;
        }
        .matiere { font-weight: bold; color: #1565C0; font-size: 11pt; padding-bottom: 3px; }
        .prof { color: #34495e; font-size: 9pt; font-style: italic; }
        .salle { background-color: #ffecb3; padding: 2px 4px; font-size: 8pt; border: 1px solid #ffe082; display: inline-block; margin-top:2px; }
    </style>
</head>
<body>

    <div class="header">
        <h1>ACADEMIX SCHOOL</h1>
        <h2>Emploi du Temps - Classe : <b>{{ classe_nom }}</b> ({{ annee }})</h2>
    </div>

    <!-- GRILLE D'EMPLOI DU TEMPS -->
    <table class="timetable">
        <thead>
            <tr>
                <th class="col-heure">HORAIRE</th>
                {% for jour in jours %}
                <th class="col-jour">{{ jour }}</th>
                {% endfor %}
            </tr>
        </thead>
        <tbody>
            {% for heure in heures_dispo %}
            <tr>
                <td class="col-heure">{{ heure }}</td>
                {% for jour in jours %}
                <td>
                    {% if grille[jour] and grille[jour][heure] %}
                        {% for c in grille[jour][heure] %}
                        <div class="creneau">
                            <div class="matiere">{{ c.matiere }} <span style="font-size: 8pt; color: #7f8c8d;">({{ c.h_deb }}-{{ c.h_fin }})</span></div>
                            <div class="prof">👤 {{ c.prof }}</div>
                            {% if c.salle %}<div class="salle">🏫 {{ c.salle }}</div>{% endif %}
                        </div>
                        {% endfor %}
                    {% else %}
                        &nbsp;
                    {% endif %}
                </td>
                {% endfor %}
            </tr>
            {% endfor %}
        </tbody>
    </table>

    <!-- FOOTER PAGE -->
    <div id="footer_content" style="text-align: center; color: #95a5a6; font-size: 9pt; border-top: 1px solid #e0e0e0; padding-top: 5px;">
        Academix School Management • Imprimé le {{ date_generation }} • L'emploi du temps est susceptible d'être ajusté par la Direction.
    </div>

</body>
</html>
"""


# =====================================================================
# FONCTIONS GÉNÉRATRICES
# =====================================================================

def render_html_to_pdf(html_str: str, output_path: str) -> bool:
    """Génère le fichier PDF final en utilisant xhtml2pdf."""
    try:
        with open(output_path, "wb") as pdf_file:
            pisa_status = pisa.CreatePDF(
                io.StringIO(html_str), 
                dest=pdf_file,
                encoding='utf-8'
            )
        return not pisa_status.err
    except Exception as e:
        print(f"Erreur de génération PDF : {e}")
        return False


def generate_bulletin_pdf(eleve: dict, classe_nom: str, trimestre: int, annee: str, bul_data: dict, output_path: str) -> bool:
    """Génère un bulletin trimestriel au format PDF."""
    env = Environment(loader=BaseLoader())
    template = env.from_string(BULLETIN_TEMPLATE)
    
    html_out = template.render(
        eleve=eleve,
        classe_nom=classe_nom,
        trimestre=trimestre,
        annee=annee,
        lignes=bul_data.get("lignes", []),
        total_pts_brut=bul_data.get("total_pts_brut", 0),
        penalite_pts=bul_data.get("penalite_pts", 0),
        total_pts_nets=bul_data.get("total_pts_nets", 0),
        moy_definitive=bul_data.get("moy_definitive", 0),
        heures_nj=bul_data.get("heures_nj", 0),
        heures_j=bul_data.get("heures_j", 0),
        date_generation=datetime.datetime.now().strftime("%d/%m/%Y à %H:%M")
    )
    
    return render_html_to_pdf(html_out, output_path)


def generate_timetable_pdf(classe_nom: str, annee: str, creneaux: list, output_path: str) -> bool:
    """Génère l'emploi du temps hebdomadaire au format PDF."""
    jours = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"]
    
    # Isoler toutes les heures de début pour chaque créneau (ex: '08:00')
    heures_set = set()
    for c in creneaux:
        h = str(c["heure_debut"])[:5]
        heures_set.add(h)
    
    if not heures_set:
        heures_dispo = [f"{h:02d}:00" for h in range(8, 18)]
    else:
        heures_dispo = sorted(list(heures_set))

    # Construire la matrice [jour][heure]
    grille = {j: {h: [] for h in heures_dispo} for j in jours}
    
    for c in creneaux:
        jour = str(c["jour"])
        h_deb = str(c["heure_debut"])[:5]
        h_fin = str(c["heure_fin"])[:5]
        
        if jour in grille and h_deb in grille[jour]:
            grille[jour][h_deb].append({
                "matiere": c["nom_matiere"],
                "prof": c.get("prof_nom", "").strip() or "N/A",
                "h_deb": h_deb,
                "h_fin": h_fin,
                "salle": c.get("salle", "")
            })

    env = Environment(loader=BaseLoader())
    template = env.from_string(TIMETABLE_TEMPLATE)
    
    html_out = template.render(
        classe_nom=classe_nom,
        annee=annee,
        jours=jours,
        heures_dispo=heures_dispo,
        grille=grille,
        date_generation=datetime.datetime.now().strftime("%d/%m/%Y")
    )
    
    return render_html_to_pdf(html_out, output_path)
