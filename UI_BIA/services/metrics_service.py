import pandas as pd
from datetime import datetime
from typing import Dict, List, Tuple, Optional


class MetricsService:
    """Serviço para cálculo de métricas do dashboard"""

    @staticmethod
    def parse_date(date_str: str) -> Optional[datetime]:
        """Converte string de data para datetime"""
        if pd.isna(date_str) or date_str == "":
            return None

        try:
            # Tenta diferentes formatos de data
            for fmt in ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y"]:
                try:
                    return datetime.strptime(str(date_str), fmt)
                except ValueError:
                    continue
            return None
        except:
            return None

    @staticmethod
    def convert_date_format(date_str: str) -> str:
        """Converte data do formato ISO (YYYY-MM-DD) para formato brasileiro (dd/mm/YYYY)"""
        if not date_str:
            return ""

        try:
            # Se já está no formato brasileiro, retorna como está
            if "/" in date_str:
                return date_str

            # Se está no formato ISO (YYYY-MM-DD), converte
            if "-" in date_str and len(date_str) == 10:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                return date_obj.strftime("%d/%m/%Y")

            return date_str
        except:
            return date_str

    @staticmethod
    def filter_data_by_date(df: pd.DataFrame, start_date: str, end_date: str) -> pd.DataFrame:
        """Filtra DataFrame por período de datas"""
        if df is None or df.empty:
            return df

        if not start_date or not end_date:
            return df

        try:
            # Converte as datas de entrada para o formato brasileiro se necessário
            start_date_br = MetricsService.convert_date_format(start_date)
            end_date_br = MetricsService.convert_date_format(end_date)

            # Tenta diferentes formatos para parsing
            start_dt = None
            end_dt = None

            # Formatos possíveis para as datas de entrada
            date_formats = ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y"]

            # Converte data inicial
            for fmt in date_formats:
                try:
                    start_dt = datetime.strptime(start_date, fmt)
                    break
                except ValueError:
                    continue

            # Converte data final
            for fmt in date_formats:
                try:
                    end_dt = datetime.strptime(end_date, fmt)
                    break
                except ValueError:
                    continue

            if start_dt is None or end_dt is None:
                print(f"Erro: Não foi possível converter as datas. Start: {start_date}, End: {end_date}")
                return df

            # Converte coluna de data do DataFrame
            df_copy = df.copy()
            df_copy['data_parsed'] = df_copy['data'].apply(MetricsService.parse_date)

            # Remove linhas com datas inválidas
            df_copy = df_copy.dropna(subset=['data_parsed'])

            # Filtra por período
            mask = (df_copy['data_parsed'] >= start_dt) & (df_copy['data_parsed'] <= end_dt)
            filtered_df = df_copy[mask].drop('data_parsed', axis=1)

            print(f"Filtro aplicado: {start_date} a {end_date}")
            print(f"Registros antes do filtro: {len(df)}")
            print(f"Registros após o filtro: {len(filtered_df)}")

            return filtered_df

        except Exception as e:
            print(f"Erro ao filtrar dados por data: {e}")
            print(f"Datas recebidas - Start: {start_date}, End: {end_date}")
            return df

    @staticmethod
    def calculate_biometry_metrics(df: pd.DataFrame, start_date: str = "", end_date: str = "") -> Dict:
        """Calcula métricas de biometria"""
        if df is None or df.empty:
            return {}

        # Filtra por período se especificado
        if start_date and end_date:
            df = MetricsService.filter_data_by_date(df, start_date, end_date)

        if df.empty:
            return {}

        try:
            # Calcula área (largura x altura)
            df_copy = df.copy()
            df_copy['area'] = pd.to_numeric(df_copy['largura'], errors='coerce') * pd.to_numeric(df_copy['altura'],
                                                                                                 errors='coerce')

            # Métricas por tanque
            metrics_by_tank = {}
            for tanque in df_copy['tanque'].unique():
                tank_data = df_copy[df_copy['tanque'] == tanque]

                metrics_by_tank[str(tanque)] = {
                    'peixes_medidos': len(tank_data),
                    'area_media': round(tank_data['area'].mean(), 2) if not tank_data['area'].isna().all() else 0.0
                }

            # Métricas gerais
            general_metrics = {
                'total_peixes_medidos': len(df_copy),
                'area_media_geral': round(df_copy['area'].mean(), 2) if not df_copy['area'].isna().all() else 0.0
            }

            return {
                'por_tanque': metrics_by_tank,
                'geral': general_metrics
            }

        except Exception as e:
            print(f"Erro ao calcular métricas de biometria: {e}")
            return {}

    @staticmethod
    def calculate_feed_metrics(df: pd.DataFrame, start_date: str = "", end_date: str = "") -> Dict:
        """Calcula métricas de ração"""
        if df is None or df.empty:
            return {}

        # Filtra por período se especificado
        if start_date and end_date:
            df = MetricsService.filter_data_by_date(df, start_date, end_date)

        if df.empty:
            return {}

        try:
            df_copy = df.copy()
            df_copy['peso'] = pd.to_numeric(df_copy['peso'], errors='coerce')

            # Métricas por tanque
            metrics_by_tank = {}
            for tanque in df_copy['tanque'].unique():
                tank_data = df_copy[df_copy['tanque'] == tanque]

                metrics_by_tank[str(tanque)] = {
                    'racao_utilizada': round(tank_data['peso'].sum(), 2) if not tank_data['peso'].isna().all() else 0.0
                }

            # Métricas gerais
            general_metrics = {
                'total_racao_utilizada': round(df_copy['peso'].sum(), 2) if not df_copy['peso'].isna().all() else 0.0
            }

            return {
                'por_tanque': metrics_by_tank,
                'geral': general_metrics
            }

        except Exception as e:
            print(f"Erro ao calcular métricas de ração: {e}")
            return {}

    @staticmethod
    def calculate_correlation_data(biometry_df: pd.DataFrame, feed_df: pd.DataFrame,
                                   start_date: str = "", end_date: str = "") -> List[Dict]:
        """Calcula dados para gráfico de correlação área vs ração por tanque"""
        try:
            bio_metrics = MetricsService.calculate_biometry_metrics(biometry_df, start_date, end_date)
            feed_metrics = MetricsService.calculate_feed_metrics(feed_df, start_date, end_date)

            if not bio_metrics or not feed_metrics:
                return []

            correlation_data = []

            # Combina dados por tanque
            for tanque in bio_metrics.get('por_tanque', {}):
                if tanque in feed_metrics.get('por_tanque', {}):
                    area_media = bio_metrics['por_tanque'][tanque]['area_media']
                    racao_utilizada = feed_metrics['por_tanque'][tanque]['racao_utilizada']

                    correlation_data.append({
                        'tanque': f"Tanque {tanque}",
                        'area_media': area_media,
                        'racao_utilizada': racao_utilizada
                    })

            return correlation_data

        except Exception as e:
            print(f"Erro ao calcular dados de correlação: {e}")
            return []