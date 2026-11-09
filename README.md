# docling-converter

Convertit en masse des pages HTML (par exemple des pages web enregistrées) en fichiers Markdown, avec [Docling](https://github.com/docling-project/docling). Le HTML est nettoyé avant conversion et les images sont exportées dans un répertoire dédié à chaque page.

## Prérequis

- Python >= 3.12
- [uv](https://docs.astral.sh/uv/) (recommandé, un `uv.lock` est fourni)
- Dépendances : `docling`, `beautifulsoup4`, `lxml`

## Installation

```powershell
uv sync
```

Ou, avec pip :

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install beautifulsoup4 docling lxml
```

## Utilisation

```powershell
uv run python convert.py [--input RÉPERTOIRE] [--output RÉPERTOIRE] [--remote-images]
```

Ou, dans l'environnement virtuel activé :

```powershell
python convert.py [--input RÉPERTOIRE] [--output RÉPERTOIRE] [--remote-images]
```

### Options

| Option | Défaut | Description |
|---|---|---|
| `--input` | `./source` | Répertoire source, parcouru récursivement pour trouver les fichiers `.html` et `.htm`. |
| `--output` | `./output` | Répertoire de destination des fichiers Markdown. |
| `--remote-images` | désactivé | Autorise le téléchargement des images distantes (`http`/`https`). Sans cette option, seules les images locales ou intégrées (`data:`) sont récupérées. |

### Exemples

```powershell
# Conversion avec les répertoires par défaut (./source -> ./output)
python convert.py

# Répertoires personnalisés
python convert.py --input C:\pages_web --output C:\markdown

# Avec téléchargement des images distantes
python convert.py --input .\source --output .\output --remote-images
```

## Fonctionnement

Pour chaque fichier HTML trouvé dans le répertoire source :

1. **Lecture** : le fichier est décodé en essayant successivement `utf-8-sig`, `utf-8`, `cp1252` puis `latin-1`.
2. **Inspection** : comptage des images locales et distantes référencées par les balises `<img>` (y compris `data-src` / `data-original` pour le lazy loading).
3. **Nettoyage** (BeautifulSoup + lxml) :
   - suppression des balises `script` et `noscript` ;
   - suppression des éléments de navigation ou décoratifs (`nav`, `footer`, `.navbar`, `.sidebar`, `.cookie-banner`, `.ads`, numéros de ligne de code, etc.) ;
   - suppression des attributs d'événements JavaScript inline (`onclick`, ...) ;
   - les styles CSS et le contenu des balises `pre`/`code` (espaces, tabulations, retours à la ligne) sont conservés.
4. **Conversion** : le HTML nettoyé est écrit dans un fichier temporaire (`_docling_clean_*.html`, placé à côté de l'original pour conserver les chemins relatifs, puis supprimé) et converti par Docling.
5. **Export** : écriture du Markdown et des images référencées.

### Structure de sortie

L'arborescence de la source est reproduite dans le répertoire de sortie :

```
output/
├── page.md
├── page_images/
│   ├── image_000000_<hash>.png
│   └── ...
└── sous-dossier/
    ├── autre.md
    └── autre_images/
```

### Journalisation

Les logs sont affichés dans la console et écrits dans `conversion.log` (dans le répertoire courant). Un résumé final indique le nombre de fichiers détectés, de réussites et d'erreurs. Un avertissement est émis si une page référence des images mais qu'aucune n'a été exportée.

### Garde-fous

- Le répertoire de sortie ne doit pas être identique au répertoire source ni se trouver à l'intérieur.
- Une erreur sur un fichier est journalisée et n'interrompt pas le traitement des suivants.

## Fichiers du projet

| Fichier | Rôle |
|---|---|
| `convert.py` | Script principal : nettoyage HTML et conversion en Markdown. |
| `main.py` | Squelette généré par `uv init` (affiche un message), sans lien avec la conversion. |
| `pyproject.toml` / `uv.lock` | Dépendances et version de Python. |
