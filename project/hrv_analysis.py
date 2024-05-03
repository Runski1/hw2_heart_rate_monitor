import ujson


class HrvAnalysis:
    def __init__(self, rri_list):
        self.rri_list = rri_list
        self.mean_rri = 0
        self.mean_hr = 0
        self.sdnn = 0
        self.rmssd = 0

    def calc_mean_rri(self):
        self.mean_rri = sum(self.rri_list) / len(self.rri_list)

    def calc_mean_hr(self):
        self.mean_hr = (60 / self.mean_rri) * 1000

    def calc_sdnn(self):
        sum = 0
        for rri in self.rri_list:
            sum += (rri - self.mean_rri) ** 2
        self.sdnn = (sum / (len(self.rri_list) - 1)) ** (0.5)

    def calc_rmssd(self):
        sum = 0
        for i in range(len(self.rri_list) - 1):
            sum += (self.rri_list[i + 1] - self.rri_list[i]) ** 2
        self.rmssd = (sum / (len(self.rri_list) - 1)) ** (0.5)

    def get_analysis(self):
        return ujson.dumps(
            {
                "mean_hr": self.mean_hr,
                "mean_ppi": self.mean_rri,
                "rmssd": self.rmssd,
                "sdnn": self.sdnn,
            }
        )

    def analyze(self):
        self.calc_mean_rri()
        self.calc_mean_hr()
        self.calc_sdnn()
        self.calc_rmssd()


def basic_hrv_analysis(rri_list):
    analysis = HrvAnalysis(rri_list)
    analysis.analyze()
    print("Data analyzed")
    return analysis.get_analysis()


if __name__ == "__main__":
    print(
        "Can't be run directly, call basic_hrv_analysis(rri_list) with a list of RRIs to run"
    )
