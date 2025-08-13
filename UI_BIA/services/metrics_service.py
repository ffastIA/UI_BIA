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
    def calculate_temporal_correlation(biometry_df: pd.DataFrame, feed_df: pd.DataFrame,
                                       start_date: str = "", end_date: str = "") -> Dict:
        """Calcula correlação temporal entre crescimento de área e ração utilizada"""
        try:
            # Filtra dados por período
            if start_date and end_date:
                biometry_filtered = MetricsService.filter_data_by_date(biometry_df, start_date, end_date)
                feed_filtered = MetricsService.filter_data_by_date(feed_df, start_date, end_date)
            else:
                biometry_filtered = biometry_df.copy()
                feed_filtered = feed_df.copy()

            if biometry_filtered.empty or feed_filtered.empty:
                return {}

            # Prepara dados de biometria
            bio_df = biometry_filtered.copy()
            bio_df['data_parsed'] = bio_df['data'].apply(MetricsService.parse_date)
            bio_df['area'] = pd.to_numeric(bio_df['largura'], errors='coerce') * pd.to_numeric(bio_df['altura'],
                                                                                               errors='coerce')
            bio_df = bio_df.dropna(subset=['data_parsed', 'area'])

            # Prepara dados de ração
            feed_df_copy = feed_filtered.copy()
            feed_df_copy['data_parsed'] = feed_df_copy['data'].apply(MetricsService.parse_date)
            feed_df_copy['peso'] = pd.to_numeric(feed_df_copy['peso'], errors='coerce')
            feed_df_copy = feed_df_copy.dropna(subset=['data_parsed', 'peso'])

            # Agrupa por tanque e data para calcular evolução temporal
            correlation_data = {}

            # Análise por tanque
            for tanque in bio_df['tanque'].unique():
                if tanque not in feed_df_copy['tanque'].values:
                    continue

                # Dados de biometria do tanque
                tank_bio = bio_df[bio_df['tanque'] == tanque].copy()
                tank_bio_grouped = tank_bio.groupby('data_parsed')['area'].mean().reset_index()
                tank_bio_grouped = tank_bio_grouped.sort_values('data_parsed')

                # Dados de ração do tanque
                tank_feed = feed_df_copy[feed_df_copy['tanque'] == tanque].copy()
                tank_feed_grouped = tank_feed.groupby('data_parsed')['peso'].sum().reset_index()
                tank_feed_grouped = tank_feed_grouped.sort_values('data_parsed')

                if len(tank_bio_grouped) < 2 or len(tank_feed_grouped) < 2:
                    continue

                # Calcula variação temporal
                area_inicial = tank_bio_grouped['area'].iloc[0]
                area_final = tank_bio_grouped['area'].iloc[-1]
                variacao_area = area_final - area_inicial
                percentual_crescimento = ((area_final - area_inicial) / area_inicial * 100) if area_inicial > 0 else 0

                racao_total = tank_feed_grouped['peso'].sum()
                racao_media_diaria = racao_total / len(tank_feed_grouped) if len(tank_feed_grouped) > 0 else 0

                # Calcula eficiência (crescimento por kg de ração)
                eficiencia = variacao_area / racao_total if racao_total > 0 else 0

                correlation_data[str(tanque)] = {
                    'area_inicial': round(area_inicial, 2),
                    'area_final': round(area_final, 2),
                    'variacao_area': round(variacao_area, 2),
                    'percentual_crescimento': round(percentual_crescimento, 2),
                    'racao_total': round(racao_total, 2),
                    'racao_media_diaria': round(racao_media_diaria, 2),
                    'eficiencia_crescimento': round(eficiencia, 4),
                    'dias_periodo': len(tank_bio_grouped)
                }

            # Análise geral (todos os tanques)
            if correlation_data:
                # Calcula médias gerais
                total_variacao_area = sum([data['variacao_area'] for data in correlation_data.values()])
                total_racao = sum([data['racao_total'] for data in correlation_data.values()])
                media_crescimento = sum([data['percentual_crescimento'] for data in correlation_data.values()]) / len(
                    correlation_data)
                eficiencia_geral = total_variacao_area / total_racao if total_racao > 0 else 0

                correlation_data['geral'] = {
                    'total_variacao_area': round(total_variacao_area, 2),
                    'total_racao': round(total_racao, 2),
                    'media_crescimento_percentual': round(media_crescimento, 2),
                    'eficiencia_geral': round(eficiencia_geral, 4),
                    'tanques_analisados': len([k for k in correlation_data.keys() if k != 'geral'])
                }

            return correlation_data

        except Exception as e:
            print(f"Erro ao calcular correlação temporal: {e}")
            return {}