from configparser import ConfigParser
from datetime import date, datetime, timedelta
import pandas as pd
from pytz import timezone
from scipy import stats

class DataLoader:
    def __init__(self, parser: ConfigParser):
        self.swiss_cases = pd.read_csv(parser.get("urls", "swiss_cases"))
        self.swiss_fatalities = pd.read_csv(parser.get("urls", "swiss_fatalities"))
        self.swiss_demography = pd.read_csv(
            parser.get("urls", "swiss_demography"), index_col=0
        )
        self.world_cases = self.__simplify_world_data(
            pd.read_csv(parser.get("urls", "world_cases"))
        )
        self.world_fataltities = self.__simplify_world_data(
            pd.read_csv(parser.get("urls", "world_fatalities"))
        )
        self.world_population = self.__get_world_population()

        self.swiss_cases_by_date = self.swiss_cases.set_index("Date")
        self.swiss_fatalities_by_date = self.swiss_fatalities.set_index("Date")

        self.swiss_cases_by_date_filled = self.swiss_cases_by_date.fillna(
            method="ffill", axis=0
        )

        self.swiss_cases_by_date_diff = self.swiss_cases_by_date_filled.diff().replace(
            0, float("nan")
        )
        self.swiss_cases_by_date_diff["date_label"] = [
            date.fromisoformat(d).strftime("%d. %m.")
            for d in self.swiss_cases_by_date_diff.index.values
        ]

        self.swiss_fatalities_by_date_diff = self.swiss_fatalities_by_date.diff().replace(
            0, float("nan")
        )

        self.swiss_cases_by_date_filled = self.swiss_cases_by_date.fillna(
            method="ffill", axis=0
        )

        self.swiss_fatalities_by_date_filled = self.swiss_fatalities_by_date.fillna(
            method="ffill", axis=0
        )

        self.swiss_case_fatality_rates = (
            self.swiss_fatalities_by_date_filled / self.swiss_cases_by_date_filled
        )

        self.swiss_cases_by_date_filled_per_capita = (
            self.__get_swiss_cases_by_date_filled_per_capita()
        )

        self.latest_date = self.__get_latest_date()
        self.updated_cantons = self.__get_updated_cantons()
        self.new_swiss_cases = self.__get_new_cases()
        self.total_swiss_cases = self.__get_total_swiss_cases()
        self.total_swiss_fatalities = self.__get_total_swiss_fatalities()
        self.swiss_case_fatality_rate = (
            self.total_swiss_fatalities / self.total_swiss_cases
        )

        # Put the date at the end
        self.swiss_cases_as_dict = self.swiss_cases.to_dict("list")
        date_tmp = self.swiss_cases_as_dict.pop("Date")
        self.swiss_cases_as_dict["Date"] = date_tmp
        self.swiss_cases_normalized_as_dict = (
            self.__get_swiss_cases_as_normalized_dict()
        )

        self.swiss_fatalities_as_dict = self.swiss_fatalities.to_dict("list")
        self.canton_labels = [
            canton
            for canton in self.swiss_cases_as_dict
            if canton != "УКРАЇНА" and canton != "Date"
        ]
        self.cantonal_centres = self.__get_cantonal_centres()

        #
        # Moving average showing development
        #

        self.moving_total = self.__get_moving_total(
            self.swiss_cases_by_date.diff()
        ).replace(0, float("nan"))
        
        #
        # World related data
        #

        self.world_case_fatality_rate = (
            self.world_fataltities.iloc[-1] / self.world_cases.iloc[-1]
        )

        self.swiss_world_cases_normalized = self.__get_swiss_world_cases_normalized()
        
        #
        # Some regression analysis on the data
        #
        self.prevalence_density_regression = self.__get_regression(
            self.swiss_demography["Density"],
            self.swiss_cases_by_date_filled_per_capita.iloc[-1],
        )

        self.cfr_age_regression = self.__get_regression(
            self.swiss_demography["O65"], self.swiss_case_fatality_rates.iloc[-1]
        )

        self.scaled_cases = self.__get_scaled_cases()

    def __get_latest_date(self):
        return self.swiss_cases.iloc[len(self.swiss_cases) - 1]["Date"]

    def __get_updated_cantons(self):
        l = len(self.swiss_cases_by_date)
        return [
            canton
            for canton in self.swiss_cases_by_date.iloc[l - 1][
                self.swiss_cases_by_date.iloc[l - 1].notnull()
            ].index
        ]

    def __get_swiss_cases_by_date_filled_per_capita(self):
        tmp = self.swiss_cases_by_date_filled.copy()

        for column in tmp:
            tmp[column] = (
                tmp[column] / self.swiss_demography["Population"][column] * 10000
            )
        return tmp

    def __get_new_cases(self):
        if (
            date.fromisoformat(self.latest_date)
            != datetime.now(timezone("Europe/Vienna")).date()
        ):
            return 0

        l = len(self.swiss_cases_by_date_filled)
        return (
            self.swiss_cases_by_date_filled.diff().iloc[l - 1].sum()
            - self.swiss_cases_by_date_filled.diff().iloc[l - 1]["УКРАЇНА"]
        )

    def __get_total_swiss_cases(self):
        return self.swiss_cases_by_date_filled.iloc[-1]["УКРАЇНА"]

    def __get_total_swiss_fatalities(self):
        return self.swiss_fatalities_by_date_filled.iloc[-1]["УКРАЇНА"]

    def __get_swiss_cases_as_normalized_dict(self):
        tmp = [
            (
                str(canton),
                [
                    round(i, 2)
                    for i in self.swiss_cases_as_dict[canton]
                    / self.swiss_demography["Population"][canton]
                    * 10000
                ],
            )
            for canton in self.swiss_cases_as_dict
            if canton != "Date"
        ]
        tmp.append(("Date", self.swiss_cases_as_dict["Date"]))
        return dict(tmp)

    def __simplify_world_data(self, df: pd.DataFrame):
        df.drop(columns=["Lat", "Long"], inplace=True)
        df["Province/State"].fillna("", inplace=True)
        df = df.rename(columns={"Country/Region": "Day"})
        df = df.groupby("Day").sum()
        df = df.T
        df.drop(
            df.columns.difference(
                ["France", "Germany", "Italy",  "Korea, South", "Spain", "US", "United Kingdom", "Switzerland",]
            ),
            1,
            inplace=True,
        )
        df.index = range(0, len(df))
        return df

    def __get_swiss_world_cases_normalized(self, min_prevalence: int = 0.1):
        tmp = self.world_cases.copy()
        tmp["УКРАЇНА"] = pd.Series(self.swiss_cases_as_dict["УКРАЇНА"])

        for column in tmp:
            tmp[column] = tmp[column] / self.world_population[column] * 10000

        tmp[tmp < min_prevalence] = 0
        for column in tmp:
            while tmp[column].iloc[0] == 0:
                tmp[column] = tmp[column].shift(-1)
        tmp.dropna(how="all", inplace=True)

        return tmp

    def __get_regression(self, x, y):
        df = pd.DataFrame([x, y])
        df = df.dropna(axis=1, how="any")
        slope, intercept, r_value, p_value, std_err = stats.linregress(
            df.iloc[0], df.iloc[1]
        )
        m = df.iloc[0].min() + (df.iloc[0].max() - df.iloc[0].min()) / 2
        return {
            "slope": slope,
            "intercept": intercept,
            "r_value": r_value,
            "p_value": p_value,
            "std_err": std_err,
            "x": [df.iloc[0].min(), m, df.iloc[0].max()],
            "y": [
                slope * df.iloc[0].min() + intercept,
                slope * m + intercept,
                slope * df.iloc[0].max() + intercept,
            ],
        }

    def __get_scaled_cases(self):
        cases = self.swiss_cases_by_date_filled.iloc[-1][0:-1]
        min_cases = cases.min()
        max_cases = cases.max()
        scaled_cases = (cases - min_cases) / (max_cases - min_cases) * (20) + 10
        return scaled_cases

    def __get_moving_total(self, df, days=7):
        offset = days - 1
        df_moving_total = df[0:0]
        for i in range(0, len(df)):
            start = max(0, i - offset)
            d = pd.Series(df.iloc[start : i + 1].sum().to_dict())
            d.name = df.index[i]
            df_moving_total = df_moving_total.append(d)

        # Add the label for the date range (previous week)
        date_labels = []
        for d in df_moving_total.index.values:
            today = date.fromisoformat(d)
            date_labels.append(
                (today - timedelta(days=7)).strftime("%d. %m.")
                + " – "
                + today.strftime("%d. %m.")
            )

        df_moving_total["date_label"] = date_labels

        return df_moving_total

    def __get_world_population(self):
        return {
            "France": 65273511,
            "Germany": 83783942,
            "Italy": 60461826,
            "Spain": 46754778,
            "US": 331002651,
            "United Kingdom": 67886011,
            "Switzerland": 8654622,
            "Korea, South": 51269185,
            "УКРАЇНА": 43799404,
        }

    def __get_cantonal_centres(self):
        return {
            "Вінницька": {"lat": 49.15, "lon": 28.41},
            "Волинська": {"lat": 50.49 + 0.8, "lon": 25.26},
            "Дніпропетровська": {"lat": 48.31 + 0.3, "lon": 35.08},
            "Донецька": {"lat": 48.03, "lon": 37.47},
            "Житомирська": {"lat": 50.18 + 0.8, "lon": 28.49},
            "Закарпатська": {"lat": 48.40 + 0.3, "lon": 22.30},
            "Запорізька": {"lat": 47.53, "lon": 35.23},
            "Івано-Франківська": {"lat": 48.56, "lon": 24.53},
            "Київська": {"lat": 50.27 - 0.3, "lon": 30.30},
            "Кіровоградська": {"lat": 48.31, "lon": 32.21},
            "Луганська": {"lat": 48.36 + 0.5, "lon": 39.22 - 0.3},
            "Львівська": {"lat": 49.53 + 0.2, "lon": 24.16},
            "Миколаївська": {"lat": 46.58 + 0.3, "lon": 32.12},
            "Одеська": {"lat": 46.29 - 0.2, "lon": 30.44},
            "Полтавська": {"lat": 49.37 + 0.1, "lon": 34.37},
            "Рівненська": {"lat": 50.39, "lon": 26.26},
            "Сумська": {"lat": 50.58 + 0.2, "lon": 34.52},
            "Тернопільська": {"lat": 49.37, "lon": 25.47},
            "Харківська": {"lat": 50.02, "lon": 36.14},
            "Херсонська": {"lat": 46.40 + 0.1, "lon": 32.42},
            "Черкаська": {"lat": 49.27 - 0.1, "lon": 32.03},
            "Чернівецька": {"lat": 48.16, "lon": 26.07},
            "Чернігівська": {"lat": 51.29 + 0.2, "lon": 31.22},
            "Київ": {"lat": 50.27, "lon": 30.30},
            "Крим": {"lat": 45.02, "lon": 35.31},
            "Севастополь": {"lat": 44.29, "lon": 33.43},
        }
