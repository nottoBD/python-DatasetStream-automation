import os
import pandas as pd
import re


def get_provider_and_year(filename):
    """
    Cette fonction extrait le nom du fournisseur et l'année du nom de fichier.

    :param filename: Nom du fichier
    :return: Tuple (provider, year) où provider est le nom du fournisseur et year est l'année
    """
    provider_names = ['voo', 'orange', 'telenet']
    provider = None
    year = None

    # Extraire le fournisseur
    for name in provider_names:
        if name in filename.lower():
            provider = name.capitalize()
            break

    # Extraire l'année
    year_match = re.search(r'\d{4}', filename)
    if year_match:
        year = year_match.group(0)

    return provider, year


def read_section_names(file_path):
    """
    Cette fonction lit les noms de sections depuis un fichier.

    :param file_path: Chemin du fichier contenant les noms de sections
    :return: Liste des noms de sections
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        section_names = [line.strip() for line in f.readlines()]
    return section_names


def parse_tsv(tsv_path, section_names):
    """
    Cette fonction analyse un fichier TSV et extrait les données.

    :param tsv_path: Chemin du fichier TSV
    :param section_names: Liste des noms de sections
    :return: Liste des paires (section, texte)
    """
    with open(tsv_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    data = []
    current_section = None

    for line in lines:
        stripped_line = line.strip()
        if stripped_line in section_names:
            current_section = stripped_line
        elif not stripped_line.isdigit() and not re.match(r'^\d{1,3}$', stripped_line):
            if current_section:
                data.append([current_section, stripped_line])

    return data


def adjust_region_columns(df):
    """
    Cette fonction ajuste les colonnes de région en fonction du texte.

    :param df: DataFrame contenant les données à ajuster
    :return: DataFrame ajusté
    """
    updated_index = []
    for text in df.index:
        original_text = text
        if re.search(r'\sW(\s|$)', text):
            df.at[text, 'Region Flanders'] = 0
            df.at[text, 'Brussels'] = 0
            df.at[text, 'Region Wallonia'] = 1
            df.at[text, 'Communauté Germanophone'] = 0
            text = re.sub(r'\sW(\s|$)', ' ', text).strip()
        elif re.search(r'\sB(\s|$)', text):
            df.at[text, 'Region Flanders'] = 0
            df.at[text, 'Brussels'] = 1
            df.at[text, 'Region Wallonia'] = 0
            df.at[text, 'Communauté Germanophone'] = 0
            text = re.sub(r'\sB(\s|$)', ' ', text).strip()
        elif re.search(r'\sG(\s|$)', text):
            df.at[text, 'Region Flanders'] = 0
            df.at[text, 'Brussels'] = 0
            df.at[text, 'Region Wallonia'] = 0
            df.at[text, 'Communauté Germanophone'] = 1
            text = re.sub(r'\sG(\s|$)', ' ', text).strip()
        else:
            df.at[text, 'Region Flanders'] = 1
            df.at[text, 'Brussels'] = 1
            df.at[text, 'Region Wallonia'] = 1
            df.at[text, 'Communauté Germanophone'] = 1

        updated_index.append(text)

    df.index = updated_index
    return df


def create_excel(data, provider, year, section_names, output_path):
    """
    Cette fonction crée un fichier Excel à partir des données fournies.

    :param data: Liste des paires (section, texte)
    :param provider: Nom du fournisseur
    :param year: Année
    :param section_names: Liste des noms de sections
    :param output_path: Chemin de sortie pour le fichier Excel
    """
    # Créer un DataFrame avec les lignes de texte comme index et les noms de sections comme colonnes
    text_rows = list(set(text for section, text in data))
    columns = ['Region Flanders', 'Brussels', 'Region Wallonia', 'Communauté Germanophone'] + section_names
    df = pd.DataFrame(0, index=text_rows, columns=columns)

    for section, text in data:
        if section in df.columns:
            df.at[text, section] = 1

    # Ajuster les colonnes de région en fonction du contenu du texte
    df = adjust_region_columns(df)

    with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
        df.to_excel(writer, startrow=5, sheet_name='Sheet1')
        workbook = writer.book
        worksheet = writer.sheets['Sheet1']

        # Définir les formats
        bold_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': 14})
        provider_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': 14,
                                               'bg_color': '#d60f8a' if provider.lower() == 'voo' else None})
        header_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter'})
        right_align_format = workbook.add_format({'align': 'right', 'valign': 'vcenter'})

        # Écrire le fournisseur et l'année, laisser les premières cellules vides
        worksheet.write('A1', '', bold_format)
        worksheet.write('A2', '', bold_format)
        worksheet.merge_range(0, 1, 0, len(columns), provider, provider_format)
        worksheet.merge_range(1, 1, 1, len(columns), year, bold_format)

        # Ajouter une ligne unicellulaire "LOCATION" au-dessus des colonnes de région
        worksheet.merge_range(2, 1, 2, 4, 'LOCATION', bold_format)

        # Ajouter une ligne unicellulaire "BOUQUET" au-dessus de toutes les colonnes de section
        worksheet.merge_range(2, 5, 2, len(columns), 'BOUQUET', bold_format)

        # Écrire les en-têtes sans le mot redondant "Chaînes"
        for i, col in enumerate(df.columns):
            display_col = col.replace('Chaînes', '').strip()
            worksheet.write(5, i + 1, display_col, header_format)

        # Écrire les noms des chaînes sur l'axe y, aligné à droite
        for i, text in enumerate(df.index):
            worksheet.write(6 + i, 0, text, right_align_format)

        # Activer les filtres
        worksheet.autofilter(5, 1, 5, len(columns))

        # Ajuster la taille des colonnes
        for i, col in enumerate(df.columns, 1):
            max_length = max((df[col].astype(str).map(len).max(), len(col.replace('Chaînes', '').strip()))) + 2
            worksheet.set_column(i, i, max_length)

        # Ajuster la largeur de la colonne des chaînes
        max_length = max((df.index.astype(str).map(len).max(), len('Channels'))) + 2
        worksheet.set_column(0, 0, max_length)


def process_files(directory):
    """
    Cette fonction traite tous les fichiers dans le répertoire donné.

    :param directory: Répertoire contenant les fichiers à traiter
    """
    for filename in os.listdir(directory):
        if filename.endswith("b.tsv"):
            base_name = os.path.splitext(filename)[0]
            provider, year = get_provider_and_year(base_name)
            if not provider or not year:
                print(f"Provider or year not found in filename: {filename}")
                continue

            tsv_path = os.path.join(directory, filename)
            a_tsv_path = os.path.join(directory, base_name[:-1] + "a.tsv")
            if not os.path.exists(a_tsv_path):
                print(f"Section names file not found: {a_tsv_path}")
                continue

            section_names = read_section_names(a_tsv_path)
            data = parse_tsv(tsv_path, section_names)
            output_path = os.path.join(directory, base_name[:-1] + "c.xlsx")
            create_excel(data, provider, year, section_names, output_path)
            print(f"Generated {output_path}")


if __name__ == "__main__":
    current_directory = '.'
    process_files(current_directory)