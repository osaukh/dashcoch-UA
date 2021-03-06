class StyleLoader:
    def __init__(self):
        self.colors = [
            "#7a8871",
            "#a359e3",
            "#91e63f",
            "#dd47ba",
            "#5ad358",
            "#6e7edc",
            "#d9dd3d",
            "#c376bc",
            "#a8cc5f",
            "#d95479",
            "#63de9f",
            "#de4f37",
            "#74deda",
            "#dd892d",
            "#71adcf",
            "#dbbd59",
            "#797ca6",
            "#4e9648",
            "#d4b7d8",
            "#8a873d",
            "#489889",
            "#b1743d",
            "#a8d5a2",
            "#a87575",
            "#d6cead",
            "#e59780",
        ]

        self.color_scale = [
            "#f2fffb",
            "#bbffeb",
            "#98ffe0",
            "#79ffd6",
            "#6df0c8",
            "#69e7c0",
            "#59dab2",
            "#45d0a5",
            "#31c194",
            "#2bb489",
            "#25a27b",
            "#1e906d",
            "#188463",
            "#157658",
            "#11684d",
            "#10523e",
        ]

        self.canton_colors = {
            "Вінницька": "#87ceeb",
            "Волинська": "#57e06f",
            "Дніпропетровська": "#57606f",
            "Донецька": "#EE5A24",
            "Житомирська": "#e9403c",
            "Закарпатська": "#F8EFBA",
            "Запорізька": "#ffffff",
            "Івано-Франківська": "#ffd134",
            "Київська": "#B53471",
            "Кіровоградська": "#eccc68",
            "Луганська": "#6D214F",
            "Львівська": "#258bcc",
            "Миколаївська": "#17a74e",
            "Одеська": "#e7423e",
            "Полтавська": "#D980FA",
            "Рівненська": "#17a74e",
            "Сумська": "#ffd829",
            "Тернопільська": "#e8423f",
            "Харківська": "#ff0000",
            "Херсонська": "#12CBC4",
            "Хмельницька": "#0271ac",
            "Черкаська": "#ffd72e",
            "Чернівецька": "#007f01",
            "Чернігівська": "#e8423f",
            "Київ": "#278bcc",
            "Крим": "#0abde3",
            "Севастополь": "#2988b9",
        }

        self.theme = {
            "background": "#252e3f",
            "foreground": "#2cfec1",
            "accent": "#7fafdf",
            "red": "#fc5c65",
            "yellow": "#fed330",
            "blue": "#45aaf2",
        }

        self.turbo = self.get_turbo()

    def get_turbo(self):
        scale = [
            "#2D384D",
            "#DB4453",
        ]

        return [(x / (len(scale) - 1), s) for x, s, in enumerate(scale)]
