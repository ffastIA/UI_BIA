import pandas as pd
import requests
from io import StringIO
from typing import Optional, Tuple


class SheetsService:
    """Serviço para carregar dados do Google Sheets"""

    @staticmethod
    def convert_sheets_url_to_csv(sheets_url: str) -> str:
        """Converte URL do Google Sheets para formato CSV"""
        if "/edit" in sheets_url:
            base_url = sheets_url.split("/edit")[0]
        else:
            base_url = sheets_url

        return f"{base_url}/export?format=csv"

    @staticmethod
    def load_sheet_data(sheets_url: str) -> Optional[pd.DataFrame]:
        """Carrega dados de uma planilha do Google Sheets"""
        try:
            csv_url = SheetsService.convert_sheets_url_to_csv(sheets_url)
            response = requests.get(csv_url, timeout=10)
            response.raise_for_status()

            # Lê o CSV em um DataFrame
            df = pd.read_csv(StringIO(response.text))
            return df

        except Exception as e:
            print(f"Erro ao carregar planilha: {e}")
            return None

    @staticmethod
    def load_all_sheets() -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
        """Carrega ambas as planilhas"""
        biometria_url = "https://docs.google.com/spreadsheets/d/1zoO2Eq-h2mx4i6p6i6bUhGCEXtVWXEZGSRYjnDa13dA"
        racao_url = "https://docs.google.com/spreadsheets/d/1i-QwgMjC9ZgWymtS_0h0amlAsu9Vu8JvEGpSzTUs_WE"

        biometria_df = SheetsService.load_sheet_data(biometria_url)
        racao_df = SheetsService.load_sheet_data(racao_url)

        return biometria_df, racao_df