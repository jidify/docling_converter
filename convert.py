
from __future__ import annotations

import argparse
import logging
import os
import tempfile
from pathlib import Path
from urllib.parse import unquote, urlparse

from bs4 import BeautifulSoup

from docling.datamodel.base_models import InputFormat
from docling_core.types.doc import ImageRefMode
from docling.datamodel.backend_options import HTMLBackendOptions
from docling.document_converter import (
    DocumentConverter,
    HTMLFormatOption,
)


# ============================================================
# CONFIGURATION
# ============================================================

HTML_EXTENSIONS = {".html", ".htm"}

# Balises supprimées du HTML temporaire
REMOVE_TAGS = [
    "script",
    "noscript",
]

# Éléments de navigation et décoratifs à supprimer.
# Ces sélecteurs sont volontairement conservateurs.
REMOVE_SELECTORS = [
    "nav",
    "footer",
    ".navbar",
    ".navigation",
    ".sidebar",
    ".cookie-banner",
    ".advertisement",
    ".ads",
    ".linenos",
    ".linenodiv",
    ".lineno",
    ".line-number",
    ".hljs-ln-numbers",
    ".blob-num",
    "td.linenos",
]

# Extensions des fichiers statiques utiles pour les contrôles
IMAGE_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif",
    ".webp", ".bmp", ".tif", ".tiff", ".svg"
}


# ============================================================
# LOGGING
# ============================================================

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(
                "conversion.log",
                encoding="utf-8",
            ),
        ],
    )


# ============================================================
# LECTURE HTML
# ============================================================

def read_html(path: Path) -> str:
    """Lit le HTML en essayant plusieurs encodages."""

    raw = path.read_bytes()

    for encoding in (
        "utf-8-sig",
        "utf-8",
        "cp1252",
        "latin-1",
    ):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue

    raise ValueError(f"Encodage non reconnu : {path}")


# ============================================================
# NETTOYAGE HTML
# ============================================================

def clean_html(html: str) -> str:
    """
    Nettoie le HTML sans modifier les espaces
    et indentations des blocs de code.
    """

    soup = BeautifulSoup(html, "lxml")

    # Suppression des scripts et éléments non documentaires
    for tag_name in REMOVE_TAGS:
        for element in soup.find_all(tag_name):
            element.decompose()

    # Suppression des éléments parasites connus
    for selector in REMOVE_SELECTORS:
        for element in soup.select(selector):
            element.decompose()

    # Suppression des événements JavaScript inline
    for tag in soup.find_all(True):
        for attr in list(tag.attrs):
            if attr.lower().startswith("on"):
                del tag.attrs[attr]

    # Ne pas supprimer les styles CSS :
    # ils peuvent contenir des informations utiles
    # pour les images et les ressources du document.

    # IMPORTANT :
    # On ne normalise jamais le contenu des balises pre/code.
    # On conserve donc les espaces, tabulations et retours ligne.

    return str(soup)


# ============================================================
# CONFIGURATION DOCLING
# ============================================================

def create_converter(
    html_file: Path,
    allow_remote_images: bool = False,
) -> DocumentConverter:
    """
    Crée un convertisseur avec le contexte du fichier HTML original.
    """

    html_options = HTMLBackendOptions(
        fetch_images=True,
        enable_local_fetch=True,
        enable_remote_fetch=allow_remote_images,

        # Le fichier original sert de base aux chemins relatifs.
        source_uri=html_file.resolve(),
    )

    return DocumentConverter(
        format_options={
            InputFormat.HTML: HTMLFormatOption(
                backend_options=html_options
            )
        }
    )


# ============================================================
# VALIDATION DES IMAGES HTML
# ============================================================

def inspect_html_images(
    html_file: Path,
    html: str,
) -> tuple[int, int]:
    """
    Compte les images locales et distantes référencées
    par les balises img.
    """

    soup = BeautifulSoup(html, "lxml")

    local_count = 0
    remote_count = 0

    for img in soup.find_all("img"):
        src = img.get("src")

        # Prend également en compte les images lazy loading
        if not src:
            src = (
                img.get("data-src")
                or img.get("data-original")
            )

        if not src:
            continue

        parsed = urlparse(src)

        if parsed.scheme in ("http", "https"):
            remote_count += 1

        elif parsed.scheme == "data":
            local_count += 1

        elif parsed.scheme in ("", "file"):
            local_count += 1

    return local_count, remote_count


# ============================================================
# CONVERSION D'UN FICHIER
# ============================================================

def convert_file(
    html_file: Path,
    source_dir: Path,
    output_dir: Path,
    allow_remote_images: bool = False,
) -> bool:

    relative_path = html_file.relative_to(source_dir)

    markdown_file = (
        output_dir / relative_path.with_suffix(".md")
    )

    # Un répertoire d'images par page
    image_dir = (
        markdown_file.parent /
        f"{markdown_file.stem}_images"
    )

    markdown_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    image_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    try:
        logging.info("Conversion : %s", relative_path)

        # Lecture du fichier original
        original_html = read_html(html_file)

        # Inspection des images
        local_images, remote_images = inspect_html_images(
            html_file,
            original_html,
        )

        logging.info(
            "Images HTML détectées : %d locales, %d distantes",
            local_images,
            remote_images,
        )

        # Nettoyage
        cleaned_html = clean_html(original_html)

        # Le fichier temporaire est placé dans le répertoire
        # d'origine pour conserver le contexte des ressources.
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".html",
            prefix="_docling_clean_",
            dir=html_file.parent,
            encoding="utf-8",
            delete=False,
        ) as temp:

            temp.write(cleaned_html)
            temp_path = Path(temp.name)

        try:
            converter = create_converter(
                html_file,
                allow_remote_images,
            )

            # Conversion
            result = converter.convert(temp_path)

            # Préfixe relatif depuis le fichier Markdown
            image_uri_prefix = (
                image_dir.relative_to(
                    markdown_file.parent
                ).as_posix() + "/"
            )

            # Export Markdown et images
            markdown_content = (
                result.document.export_to_markdown(
                    image_mode=ImageRefMode.REFERENCED,
                    image_dir=image_dir,
                    image_uri_prefix=image_uri_prefix,
                )
            )

            markdown_file.write_text(
                markdown_content,
                encoding="utf-8",
            )

        finally:
            # Suppression du HTML temporaire
            temp_path.unlink(missing_ok=True)

        # Contrôle des images exportées
        exported_images = [
            image
            for image in image_dir.iterdir()
            if image.is_file()
        ]

        logging.info(
            "Markdown créé : %s",
            markdown_file,
        )

        logging.info(
            "Images exportées : %d",
            len(exported_images),
        )

        if not exported_images and local_images + remote_images > 0:
            logging.warning(
                "Aucune image exportée pour %s",
                html_file,
            )

        # Contrôle des références Markdown
        if exported_images:
            logging.info(
                "Répertoire images : %s",
                image_dir,
            )

        return True

    except Exception:
        logging.exception(
            "Erreur pendant la conversion de %s",
            html_file,
        )
        return False


# ============================================================
# TRAITEMENT RECURSIF
# ============================================================

def convert_directory(
    source_dir: Path,
    output_dir: Path,
    allow_remote_images: bool = False,
):

    source_dir = source_dir.resolve()
    output_dir = output_dir.resolve()

    if not source_dir.is_dir():
        raise SystemExit(
            f"Répertoire source introuvable : {source_dir}"
        )

    if (
        source_dir == output_dir
        or source_dir in output_dir.parents
    ):
        raise SystemExit(
            "Le répertoire de sortie ne doit pas être "
            "identique à la source ni situé à l'intérieur."
        )

    # Détection des HTML
    html_files = sorted(
        file
        for file in source_dir.rglob("*")
        if file.is_file()
        and file.suffix.lower() in HTML_EXTENSIONS
        and not file.name.startswith("_docling_clean_")
    )

    if not html_files:
        logging.warning("Aucun fichier HTML trouvé.")
        return

    logging.info(
        "%d fichiers HTML détectés.",
        len(html_files),
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    success = 0
    errors = 0

    for index, html_file in enumerate(
        html_files,
        start=1,
    ):

        logging.info(
            "[%d/%d] %s",
            index,
            len(html_files),
            html_file.relative_to(source_dir),
        )

        result = convert_file(
            html_file=html_file,
            source_dir=source_dir,
            output_dir=output_dir,
            allow_remote_images=allow_remote_images,
        )

        if result:
            success += 1
        else:
            errors += 1

    # Résumé
    logging.info("=" * 60)
    logging.info("CONVERSION TERMINÉE")
    logging.info("=" * 60)
    logging.info("Fichiers HTML : %d", len(html_files))
    logging.info("Réussites     : %d", success)
    logging.info("Erreurs       : %d", errors)
    logging.info("Sortie        : %s", output_dir)


# ============================================================
# POINT D'ENTRÉE
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Nettoyage HTML et conversion Markdown "
            "avec Docling"
        )
    )

    parser.add_argument(
        "--input",
        type=Path,
        default=Path("./source"),
        help="Répertoire source",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path("./output"),
        help="Répertoire de destination",
    )

    parser.add_argument(
        "--remote-images",
        action="store_true",
        help="Autoriser le téléchargement des images distantes",
    )

    args = parser.parse_args()

    setup_logging()

    convert_directory(
        source_dir=args.input,
        output_dir=args.output,
        allow_remote_images=args.remote_images,
    )


if __name__ == "__main__":
    main()
