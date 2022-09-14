import pickle
import time
from datetime import datetime
from functools import wraps

import pyotp
import requests
import stepn_password

url_front = "https://m.stepn.com"
url_api = "https://api.stepn.com/run"
url_pics = "https://res.stepn.com/imgOut"

params_orderlist = [
    "order",  # Sorting
    "chain",  # Blockchain id
    "refresh",  # Force refresh
    "page",  # Page index
    "type",  # Sneakers || Shoeboxes
    "gType",  # Don't know
    "quality",  # Common, Uncommon, Rare, Epic, Legendary
    "level",  # Level of the shoes
    "bread",  # Number of mints
]

mapping_chain = {
    "sol": 103,
    "bnb": 104,
    "eth": 101,
}

mapping_type = {
    "sneakers_all": 600,
    "sneakers_walker": 601,
    "sneakers_jogger": 602,
    "sneakers_runner": 603,
    "sneakers_trainer": 604,
    "shoeboxes_all": 301,
}

mapping_order = {
    "lowest_price": 2001,
    "highest_price": 2002,
    "latest": 1002,
}

mapping_quality = {
    "common": 1,
    "uncommon": 2,
    "rare": 3,
    "epic": 4,
    "legendary": 5,
}

mapping_response_attrs = {
    0: "Efficiency",
    1: "Luck",
    2: "Comfort",
    3: "Resilience",
    4: "Unknown",
}

mapping_chain_reversed = {y: x for x, y in mapping_chain.items()}
mapping_type_reversed = {y: x for x, y in mapping_type.items()}
mapping_order_reversed = {y: x for x, y in mapping_order.items()}
mapping_quality_reversed = {y: x for x, y in mapping_quality.items()}
mapping_response_attrs_reversed = {y: x for x, y in mapping_response_attrs.items()}


def safe_evolution(a, b, default="N/A"):
    try:
        return round(((a - b) / b) * 100, 2)
    except Exception:
        return default


def safe_percent(a, b, default="N/A"):
    try:
        return round(a * b / 100, 2)
    except Exception:
        return default


def safe_add_percent(a, b, default="N/A"):
    try:
        to_add = safe_percent(a, b, default)
        return round(a + to_add, 2)
    except Exception:
        return default


def safe_minus_percent(a, b, default="N/A"):
    try:
        to_dim = safe_percent(a, b, default)
        return round(a - to_dim, 2)
    except Exception:
        return default


class StepnNotFound(Exception):
    """ Raised when 'Order does not exist'"""

    def __init__(self, message="Order does not exist"):
        self.message = message


class StepnNotAuthorized(Exception):
    """ Raised when 'Player hasnt logged in yet'"""

    def __init__(self, message="Player hasnt logged in yet"):
        self.message = message


def http_stepn_watcher(function):
    @wraps(function)
    def _http_stepn_watcher(*args, **kwargs):
        try:
            response = function(*args, **kwargs)

            response_json = response.json()
            match response_json.get('code'):
                case 0:
                    return response_json
                case 102001:
                    print("NotAuthorized")
                    raise StepnNotAuthorized()
                case 212017:
                    print("NotFound")
                    raise StepnNotFound()

            if response_json.get('code'):
                raise Exception(response_json.get('code'), response_json.get('msg'))

        except Exception as e:
            raise e

    return _http_stepn_watcher


class StepnRequest(object):
    session = requests.session()

    __email: str
    __password: str
    __google_2auth_secret: str

    sessionID = None

    def __init__(self, email, password, google_2auth_secret=None):
        self.__email = email
        self.__password = password
        self.__google_2auth_secret = google_2auth_secret

        attempt = 3
        success = False
        while attempt > 0:
            if self.ensure_connection():
                success = True
                break
            attempt -= 1

        if not success:
            raise Exception('Impossible to ensure_connection')

    def ensure_connection(self):
        if not self.session.cookies:
            self.load_cookies()

        try:
            response = self.get_userbasic()

            if response and response.get("code") == 0:
                return True
            else:
                raise ConnectionError
        except ConnectionError:
            self.get_login()
        except StepnNotAuthorized:
            self.get_login()

    def load_cookies(self):
        try:
            with open('cookies', 'rb') as f:
                self.session.cookies.update(pickle.load(f))
                self.sessionID = self.session.cookies.get('sessionID')
        except FileNotFoundError:
            return

    @http_stepn_watcher
    def get_login(self, ):
        encoded_password = stepn_password.hash_password(self.__email, self.__password)

        google_2auth_code = pyotp.TOTP(self.__google_2auth_secret).now()

        url = self.creates_url_params(
            endpoint='login',
            account=self.__email,
            password=encoded_password,
            type=3,
            deviceInfo="web"
        )

        response = self.session.get(url)

        try:
            self.sessionID = response.json()["data"]['sessionID']
        except Exception:
            pass

        url = self.creates_url_params(
            endpoint='doCodeCheck',
            codeData=f'2%3A{google_2auth_code}',
            sessionID=self.sessionID
        )
        response = self.session.get(url)

        self.session.cookies.set("sessionID", self.sessionID)

        with open('cookies', 'wb') as f:
            pickle.dump(self.session.cookies, f)

        return response

    @http_stepn_watcher
    def get_userbasic(self):
        url = self.creates_url_params(endpoint='userbasic', sessionID=self.sessionID)

        response = self.session.get(url)

        return response

    @http_stepn_watcher
    def get_orderlist(self, **kwargs):
        """
        params_example = {
            "order": mapping_order["lowest_price"],
            "chain": mapping_chain["sol"],
            "refresh": "true",
            "page": 0,
            "type": mapping_type["sneakers_all"],
            "gType": "",
            "quality": "",
            "level": "",
            "bread": "",
        }

        Response sample :
        {"code":0,"data":[{"id":206356264,"otd":202770238,"time":0,"propID":122675762455,"img":"4/12/m21870b_881dff4064fffdf4e31fe422e12eff86c52d_67.png","dataID":100107,"sellPrice":1160000,"hp":100,"level":5,"quality":1,"mint":2,"addRatio":40,"lifeRatio":10000,"v1":12,"v2":56,"speedMax":556,"speedMin":223},{"id":206356643,"otd":406100437,"time":0,"propID":98090004455,"img":"34/28/m218706_299b0888a7b4e2ea8388ff886cf27b887c27_67.png","dataID":100102,"sellPrice":1160000,"hp":100,"level":5,"quality":1,"mint":2,"addRatio":40,"lifeRatio":10000,"v1":22,"v2":74,"speedMax":556,"speedMin":223},{"id":206359332,"otd":300398906,"time":0,"propID":35307082741,"img":"37/14/m218715_9d88ffffd93aff6f88888817ab0cffc921ff_67.png","dataID":100117,"sellPrice":1160000,"hp":100,"level":5,"quality":1,"mint":3,"addRatio":40,"lifeRatio":10000,"v1":176,"v2":38,"speedMax":556,"speedMin":223},{"id":206361847,"otd":217875405,"time":0,"propID":130751991169,"img":"37/22/m218706_09936d879ee5cbae0f2c95ff134374dafd9e_67.png","dataID":100102,"sellPrice":1160000,"hp":100,"level":5,"quality":1,"mint":1,"addRatio":40,"lifeRatio":10000,"v1":42,"v2":62,"speedMax":556,"speedMin":223},{"id":206362572,"otd":443629278,"time":0,"propID":77196876791,"img":"6/47/m218715_886a04e383e21dccd37d510011228616d6a1_67.png","dataID":100117,"sellPrice":1160000,"hp":100,"level":5,"quality":1,"mint":1,"addRatio":40,"lifeRatio":10000,"v1":35,"v2":55,"speedMax":556,"speedMin":223},{"id":206363043,"otd":377116057,"time":0,"propID":158021195125,"img":"26/29/m2186fd_8888ffff7688b288ef0f2b88883eff33d188_67.png","dataID":100093,"sellPrice":1160000,"hp":100,"level":9,"quality":1,"mint":2,"addRatio":40,"lifeRatio":10000,"v1":380,"v2":60,"speedMax":278,"speedMin":112},{"id":206360688,"otd":781690499,"time":0,"propID":185378476743,"img":"6/28/m21870b_9b4907d7277dcbae0f88d57f816cb8b453c4_67.png","dataID":100107,"sellPrice":1167000,"hp":100,"level":9,"quality":1,"mint":2,"addRatio":40,"lifeRatio":10000,"v1":388,"v2":93,"speedMax":556,"speedMin":223},{"id":206356764,"otd":878882891,"time":0,"propID":135649813231,"img":"1/32/m218710_88adff8888ffb288ef883eff33d188ff7688_67.png","dataID":100112,"sellPrice":1168000,"hp":100,"level":5,"quality":1,"mint":2,"addRatio":40,"lifeRatio":10000,"v1":276,"v2":83,"speedMax":556,"speedMin":223},{"id":206355886,"otd":437675434,"time":0,"propID":108620737923,"img":"8/4/m218715_1e318888676f888cffff163b8873ff905fff_67.png","dataID":100117,"sellPrice":1169000,"hp":100,"level":9,"quality":1,"mint":2,"addRatio":40,"lifeRatio":10000,"v1":405,"v2":38,"speedMax":556,"speedMin":223},{"id":206322028,"otd":540550207,"time":0,"propID":174981272319,"img":"3/12/m218706_96f4eb8ee02bc53288144088022cea35ddf7_67.png","dataID":100102,"sellPrice":1170000,"hp":100,"level":5,"quality":1,"mint":3,"addRatio":40,"lifeRatio":10000,"v1":48,"v2":83,"speedMax":556,"speedMin":223},{"id":206322363,"otd":572366114,"time":0,"propID":80298959575,"img":"6/22/m218710_0b94448951cf289bce5afbff59adce646309_67.png","dataID":100112,"sellPrice":1170000,"hp":100,"level":5,"quality":1,"mint":2,"addRatio":40,"lifeRatio":10000,"v1":98,"v2":96,"speedMax":556,"speedMin":223},{"id":206322484,"otd":649842892,"time":0,"propID":72288193677,"img":"17/4/m218701_0ff724e0beffb6de16af472e7fc6d0159effde67ff_67.png","dataID":100097,"sellPrice":1170000,"hp":100,"level":5,"quality":1,"mint":3,"addRatio":40,"lifeRatio":10000,"v1":191,"v2":72,"speedMax":556,"speedMin":223},{"id":206322797,"otd":829291771,"time":0,"propID":63678325511,"img":"0/13/m218715_b453c4879ee58890ffd7277d816cb82c95ff_67.png","dataID":100117,"sellPrice":1170000,"hp":100,"level":5,"quality":1,"mint":1,"addRatio":40,"lifeRatio":10000,"v1":84,"v2":42,"speedMax":556,"speedMin":223},{"id":206324029,"otd":871175911,"time":0,"propID":145761464569,"img":"19/41/m21870b_88feff05b9ca1b2ba57682ff8891ffffd088_67.png","dataID":100107,"sellPrice":1170000,"hp":100,"level":5,"quality":1,"mint":3,"addRatio":40,"lifeRatio":10000,"v1":66,"v2":16,"speedMax":556,"speedMin":223},{"id":206341221,"otd":853826250,"time":0,"propID":197141512943,"img":"5/28/m2186f8_2c95ff888807d7277dcbae0f13437409936d_67.png","dataID":100088,"sellPrice":1170000,"hp":100,"level":5,"quality":1,"mint":2,"addRatio":40,"lifeRatio":10000,"v1":51,"v2":89,"speedMax":278,"speedMin":112},{"id":206347216,"otd":627378123,"time":0,"propID":180529111699,"img":"45/26/m21870b_886683ff1e26db8bfaaf9d8888deff1d7d82_67.png","dataID":100107,"sellPrice":1170000,"hp":100,"level":5,"quality":1,"mint":2,"addRatio":40,"lifeRatio":10000,"v1":203,"v2":38,"speedMax":556,"speedMin":223},{"id":206352925,"otd":538205018,"time":0,"propID":138715960773,"img":"14/43/m21870b_78d2ff196a5009936dec9c9c4bbcf5fa0035_67.png","dataID":100107,"sellPrice":1170000,"hp":100,"level":5,"quality":1,"mint":2,"addRatio":40,"lifeRatio":10000,"v1":12,"v2":65,"speedMax":556,"speedMin":223},{"id":206353154,"otd":650130168,"time":0,"propID":176138618815,"img":"14/5/18710_fed.png","dataID":100112,"sellPrice":1170000,"hp":100,"level":5,"quality":1,"mint":2,"addRatio":40,"lifeRatio":10000,"v1":98,"v2":11,"speedMax":556,"speedMin":223},{"id":206353351,"otd":618638798,"time":0,"propID":68895635903,"img":"38/33/m218706_ff6f88c921ff16dd841b5488ffd93a2b7a7a_67.png","dataID":100102,"sellPrice":1170000,"hp":100,"level":5,"quality":1,"mint":2,"addRatio":40,"lifeRatio":10000,"v1":78,"v2":11,"speedMax":556,"speedMin":223},{"id":206353584,"otd":737490035,"time":0,"propID":51046775615,"img":"17/34/18715_d04.png","dataID":100117,"sellPrice":1170000,"hp":100,"level":5,"quality":1,"mint":3,"addRatio":40,"lifeRatio":10000,"v1":29,"v2":85,"speedMax":556,"speedMin":223},{"id":206353788,"otd":820877554,"time":0,"propID":70459498097,"img":"36/17/m218715_af472eb6de16159effe0beffde67ff0ff724_67.png","dataID":100117,"sellPrice":1170000,"hp":100,"level":5,"quality":1,"mint":2,"addRatio":40,"lifeRatio":10000,"v1":75,"v2":34,"speedMax":556,"speedMin":223},{"id":206359744,"otd":928247841,"time":0,"propID":126580295437,"img":"24/32/186fd_466.png","dataID":100093,"sellPrice":1170000,"hp":100,"level":5,"quality":1,"mint":2,"addRatio":40,"lifeRatio":10000,"v1":26,"v2":95,"speedMax":278,"speedMin":112},{"id":206361133,"otd":117376374,"time":0,"propID":173372442887,"img":"49/38/m2186d6_b78855639c9c4eff80a2203dbe1588674dff_67.png","dataID":100054,"sellPrice":1170000,"hp":100,"level":9,"quality":1,"mint":2,"addRatio":40,"lifeRatio":10000,"v1":334,"v2":39,"speedMax":167,"speedMin":28},{"id":206361690,"otd":757725552,"time":0,"propID":89200269455,"img":"21/13/m2186d6_d67e88888eff83bbffe2b188ffc501ea88ff_67.png","dataID":100054,"sellPrice":1170000,"hp":100,"level":6,"quality":1,"mint":2,"addRatio":40,"lifeRatio":10000,"v1":33,"v2":27,"speedMax":167,"speedMin":28},{"id":206361725,"otd":303297061,"time":0,"propID":97782923521,"img":"50/45/m2186e5_ea88ffd67e8883bbffff7c12666688ff1689_67.png","dataID":100069,"sellPrice":1170000,"hp":100,"level":6,"quality":1,"mint":2,"addRatio":40,"lifeRatio":10000,"v1":241,"v2":76,"speedMax":167,"speedMin":28},{"id":206361863,"otd":899508387,"time":0,"propID":93420408743,"img":"43/40/m2186e5_c422ff3b4438edcaff2590fff9f0ff888eff_67.png","dataID":100069,"sellPrice":1170000,"hp":100,"level":5,"quality":1,"mint":2,"addRatio":40,"lifeRatio":10000,"v1":37,"v2":82,"speedMax":167,"speedMin":28},{"id":206362573,"otd":195473499,"time":0,"propID":137803365131,"img":"40/46/m2186ee_83bbffd67e88ffc5011e3188eaa588fffd86_67.png","dataID":100078,"sellPrice":1170000,"hp":100,"level":5,"quality":1,"mint":2,"addRatio":40,"lifeRatio":10000,"v1":236,"v2":69,"speedMax":278,"speedMin":112},{"id":206363433,"otd":981502447,"time":0,"propID":164634915329,"img":"26/5/m2186f3_88177f7c88070fd5f5a4db4c01ad6fbf87e4_67.png","dataID":100083,"sellPrice":1170000,"hp":100,"level":0,"quality":1,"mint":0,"addRatio":40,"lifeRatio":10000,"v1":11,"v2":30,"speedMax":278,"speedMin":112},{"id":206356710,"otd":926988824,"time":0,"propID":135175764371,"img":"11/38/m2186e0_9c3eff1a276fff012231cdf4fe934d4c8835_67.png","dataID":100064,"sellPrice":1173000,"hp":100,"level":5,"quality":1,"mint":2,"addRatio":40,"lifeRatio":10000,"v1":199,"v2":35,"speedMax":167,"speedMin":28},{"id":206348426,"otd":303643937,"time":0,"propID":188092592737,"img":"26/46/m218706_88d0ff1b802b4e4aff6acbfb1a88ff4d3d20_67.png","dataID":100102,"sellPrice":1175000,"hp":100,"level":5,"quality":1,"mint":2,"addRatio":40,"lifeRatio":10000,"v1":53,"v2":35,"speedMax":556,"speedMin":223},{"id":206349037,"otd":821981045,"time":0,"propID":166379442991,"img":"4/17/18710_23d.png","dataID":100112,"sellPrice":1175000,"hp":100,"level":5,"quality":1,"mint":3,"addRatio":40,"lifeRatio":10000,"v1":240,"v2":20,"speedMax":556,"speedMin":223},{"id":206357733,"otd":197598793,"time":0,"propID":192792223709,"img":"44/20/m2186d6_f7c5ff0c46ff675f107f5588f2a01f55d09b_67.png","dataID":100054,"sellPrice":1175000,"hp":100,"level":6,"quality":1,"mint":2,"addRatio":40,"lifeRatio":10000,"v1":243,"v2":14,"speedMax":167,"speedMin":28},{"id":206358194,"otd":669304042,"time":0,"propID":167889046199,"img":"27/20/m2186e0_88a6ff039b2f88ec1e88c4ff51eaa31b30ff_67.png","dataID":100064,"sellPrice":1175000,"hp":100,"level":5,"quality":1,"mint":3,"addRatio":40,"lifeRatio":10000,"v1":197,"v2":82,"speedMax":167,"speedMin":28},{"id":206358361,"otd":735065919,"time":0,"propID":176475954161,"img":"45/34/m21870b_a69488f89dff9f2722ff6e059d6c079057ff_67.png","dataID":100107,"sellPrice":1175000,"hp":100,"level":0,"quality":1,"mint":0,"addRatio":40,"lifeRatio":10000,"v1":74,"v2":32,"speedMax":556,"speedMin":223},{"id":206357202,"otd":344159329,"time":0,"propID":182889891373,"img":"40/9/m2186e0_dd1d04eadb711c4cfb80b0effe03887b9027_67.png","dataID":100064,"sellPrice":1176000,"hp":100,"level":5,"quality":1,"mint":2,"addRatio":40,"lifeRatio":10000,"v1":153,"v2":28,"speedMax":167,"speedMin":28},{"id":206363385,"otd":145206197,"time":0,"propID":21502775969,"img":"36/48/m2186fd_35ddf788deffc53288144088c888ff4a73ec_67.png","dataID":100093,"sellPrice":1177770,"hp":100,"level":9,"quality":1,"mint":3,"addRatio":40,"lifeRatio":10000,"v1":389,"v2":55,"speedMax":278,"speedMin":112},{"id":206349907,"otd":687592381,"time":0,"propID":185925270881,"img":"50/3/m21870b_887c276cf27bf6feff299b084343b388ff88_67.png","dataID":100107,"sellPrice":1177999,"hp":100,"level":5,"quality":1,"mint":2,"addRatio":40,"lifeRatio":10000,"v1":59,"v2":37,"speedMax":556,"speedMin":223},{"id":206344533,"otd":846149321,"time":0,"propID":28985883597,"img":"46/26/m21870b_af3188c8f68850884bff058bd840ffa478f7_67.png","dataID":100107,"sellPrice":1178000,"hp":100,"level":5,"quality":1,"mint":2,"addRatio":40,"lifeRatio":10000,"v1":15,"v2":57,"speedMax":556,"speedMin":223},{"id":206344845,"otd":974882141,"time":0,"propID":112830348367,"img":"29/11/m218706_9d88ff1b54882b7a7ac921ff16dd84ffd93a_67.png","dataID":100102,"sellPrice":1178000,"hp":100,"level":5,"quality":1,"mint":2,"addRatio":40,"lifeRatio":10000,"v1":40,"v2":86,"speedMax":556,"speedMin":223},{"id":206345544,"otd":217378776,"time":0,"propID":86418665457,"img":"16/27/m21870b_8890ffd7277dcbae0f2c95ffb453c4635288_67.png","dataID":100107,"sellPrice":1178000,"hp":100,"level":5,"quality":1,"mint":2,"addRatio":40,"lifeRatio":10000,"v1":48,"v2":75,"speedMax":556,"speedMin":223},{"id":206345800,"otd":263644432,"time":0,"propID":184125495805,"img":"25/6/m218710_de67ffaf472e46d4ffb6de16e0beff0ff724_67.png","dataID":100112,"sellPrice":1178000,"hp":100,"level":5,"quality":1,"mint":2,"addRatio":40,"lifeRatio":10000,"v1":38,"v2":64,"speedMax":556,"speedMin":223},{"id":206346028,"otd":664037675,"time":0,"propID":90964100815,"img":"26/39/m218710_fffd8688ddff83bbffd67e88ea88ffff1689_67.png","dataID":100112,"sellPrice":1178000,"hp":100,"level":5,"quality":1,"mint":2,"addRatio":40,"lifeRatio":10000,"v1":24,"v2":29,"speedMax":556,"speedMin":223},{"id":206346717,"otd":720697858,"time":0,"propID":167125454165,"img":"29/43/m218701_abb7ff70f1436375ff3395518885ffc19595423663_67.png","dataID":100097,"sellPrice":1178000,"hp":100,"level":5,"quality":1,"mint":2,"addRatio":40,"lifeRatio":10000,"v1":12,"v2":60,"speedMax":556,"speedMin":223},{"id":206349997,"otd":915446517,"time":0,"propID":148448146367,"img":"44/11/m218701_ffc50183bbffff16899613ff88ddff9730ffe82bff_67.png","dataID":100097,"sellPrice":1178000,"hp":100,"level":0,"quality":1,"mint":0,"addRatio":40,"lifeRatio":10000,"v1":48,"v2":17,"speedMax":556,"speedMin":223},{"id":206338494,"otd":767428335,"time":0,"propID":77667085703,"img":"44/31/m218710_3e885488608a88f65c1288fff24e8888aeff_67.png","dataID":100112,"sellPrice":1179000,"hp":100,"level":5,"quality":1,"mint":2,"addRatio":40,"lifeRatio":10000,"v1":51,"v2":88,"speedMax":556,"speedMin":223},{"id":206345220,"otd":961992923,"time":0,"propID":31847201349,"img":"18/12/m218710_88b57f9d305c64630959adce289bce5afbff_67.png","dataID":100112,"sellPrice":1179000,"hp":100,"level":5,"quality":1,"mint":2,"addRatio":40,"lifeRatio":10000,"v1":83,"v2":32,"speedMax":556,"speedMin":223},{"id":206321159,"otd":513753231,"time":0,"propID":59452408893,"img":"26/45/18715_1fe.png","dataID":100117,"sellPrice":1180000,"hp":100,"level":5,"quality":1,"mint":3,"addRatio":40,"lifeRatio":10000,"v1":266,"v2":43,"speedMax":556,"speedMin":223},{"id":206330324,"otd":677856786,"time":0,"propID":28976578889,"img":"6/16/m218710_883affd2c6ffd840ff96cdc3af3188ff42ff_67.png","dataID":100112,"sellPrice":1180000,"hp":100,"level":5,"quality":1,"mint":2,"addRatio":40,"lifeRatio":10000,"v1":32,"v2":32,"speedMax":556,"speedMin":223},{"id":206330562,"otd":415077911,"time":0,"propID":195394145549,"img":"13/27/m218715_e383e266aefe1dccd3112286b4b12b2d60a5_67.png","dataID":100117,"sellPrice":1180000,"hp":100,"level":5,"quality":1,"mint":2,"addRatio":40,"lifeRatio":10000,"v1":60,"v2":100,"speedMax":556,"speedMin":223},{"id":206331520,"otd":654647450,"time":0,"propID":93100724091,"img":"3/30/m218710_ffd93affd111976a9c5b88ff8dbb1be43809_67.png","dataID":100112,"sellPrice":1180000,"hp":100,"level":9,"quality":1,"mint":2,"addRatio":40,"lifeRatio":10000,"v1":373,"v2":43,"speedMax":556,"speedMin":223},{"id":206332443,"otd":274304649,"time":0,"propID":84349640931,"img":"14/3/m218715_8863df112286b4b12bb33614413065e383e2_67.png","dataID":100117,"sellPrice":1180000,"hp":100,"level":0,"quality":1,"mint":0,"addRatio":40,"lifeRatio":10000,"v1":56,"v2":25,"speedMax":556,"speedMin":223},{"id":206332542,"otd":235070544,"time":0,"propID":73515159853,"img":"7/43/m218710_1e3188ae01ff439788979b7dff163b88676f_67.png","dataID":100112,"sellPrice":1180000,"hp":100,"level":6,"quality":1,"mint":2,"addRatio":40,"lifeRatio":10000,"v1":27,"v2":54,"speedMax":556,"speedMin":223},{"id":206340533,"otd":893956501,"time":0,"propID":94724818261,"img":"10/26/m218701_dcb01efdf4e38842ff881dff1fe42288a69ef152ff_67.png","dataID":100097,"sellPrice":1180000,"hp":100,"level":5,"quality":1,"mint":2,"addRatio":40,"lifeRatio":10000,"v1":89,"v2":92,"speedMax":556,"speedMin":223},{"id":206343801,"otd":615854823,"time":0,"propID":163207732103,"img":"7/38/m218710_f7c5ff675f100c46ff886dff3ef2b855d09b_67.png","dataID":100112,"sellPrice":1180000,"hp":100,"level":1,"quality":1,"mint":0,"addRatio":40,"lifeRatio":10000,"v1":76,"v2":15,"speedMax":556,"speedMin":223},{"id":206355601,"otd":248427093,"time":0,"propID":62239841011,"img":"46/46/186e0_979.png","dataID":100064,"sellPrice":1180000,"hp":100,"level":5,"quality":1,"mint":3,"addRatio":40,"lifeRatio":10000,"v1":20,"v2":88,"speedMax":167,"speedMin":28},{"id":206356569,"otd":814266284,"time":0,"propID":22431348811,"img":"1/41/m2186d6_ff1e26af9d88657488db8bfa8848ff1d7d82_67.png","dataID":100054,"sellPrice":1180000,"hp":100,"level":5,"quality":1,"mint":2,"addRatio":40,"lifeRatio":10000,"v1":54,"v2":14,"speedMax":167,"speedMin":28},{"id":206357938,"otd":675817127,"time":0,"propID":114759554655,"img":"24/9/m2186fd_b0831410b17d2525f5f4b2d0614c8ca595b5_67.png","dataID":100093,"sellPrice":1180000,"hp":100,"level":5,"quality":1,"mint":2,"addRatio":40,"lifeRatio":10000,"v1":184,"v2":89,"speedMax":278,"speedMin":112},{"id":206360485,"otd":795208347,"time":0,"propID":44765459797,"img":"39/35/186f8_4a7.png","dataID":100088,"sellPrice":1180000,"hp":100,"level":5,"quality":1,"mint":2,"addRatio":40,"lifeRatio":10000,"v1":23,"v2":97,"speedMax":278,"speedMin":112},{"id":206361667,"otd":813859557,"time":0,"propID":45443851099,"img":"16/48/m2186db_d6545f329388881dff4064ff88bce6e12eff_67.png","dataID":100059,"sellPrice":1180000,"hp":100,"level":5,"quality":1,"mint":2,"addRatio":40,"lifeRatio":10000,"v1":205,"v2":74,"speedMax":167,"speedMin":28},{"id":206321926,"otd":332567211,"time":0,"propID":159642903639,"img":"10/39/m21870b_eb66ff9353ffde4324de67ff40cd2faf472e_67.png","dataID":100107,"sellPrice":1182000,"hp":100,"level":5,"quality":1,"mint":2,"addRatio":40,"lifeRatio":10000,"v1":229,"v2":59,"speedMax":556,"speedMin":223}]}
        """
        url = self.creates_url_params(endpoint='orderlist', **kwargs, sessionID=self.sessionID)

        response = self.session.get(url)
        return response

    @http_stepn_watcher
    def get_orderdata(self, order_id):
        """
        Get one specific order.

        Response sample:
        {'id': 115399065777, 'state': 1230, 'type': 3, 'dataID': 100102, 'chain': 103, 'level': 5, 'quality': 1, 'hp': 100, 'isRun': False, 'remain': 200, 'attrs': [49, 53, 17, 57, 0, 0, 0, 0, 0, 0, 0, 0], 'endTime': 0, 'upLeveTime': 21600000, 'coolDownE': 86400000, 'canSend': False, 'price': 0, 'speedMin': 223, 'speedMax': 556, 'breed': 2, 'breedT': 1654351684873, 'otd': 500954417, 'hpLimit': 100, 'isTest': False, 'shoeImg': '25/1/m218706_f24e88887e635188bd88f65c88608a3e8854_67.png', 'lifeRatio': 10000, 'relatives': [{'type': 1, 'otd': 353098287, 'dataId': 100064, 'img': '2/44/m2186e0_8299cca7884e674dff639c9cb78855a2203d_67.png', 'shoeId': 151624525461}, {'type': 1, 'otd': 426386838, 'dataId': 100112, 'img': '27/42/m218710_4d6dff27374faafdff8885ffd755087f1268_67.png', 'shoeId': 160216503009}, {'type': 2, 'otd': 852544210, 'dataId': 100097, 'img': '35/10/m218701_88bce6f988e78842ff1fe422dcb01e8896ffd002ff_67.png', 'shoeId': 109258989309}, {'type': 2, 'otd': 535668981, 'dataId': 100102, 'img': '49/2/m218706_a7234235544dce55c3c497954b52f2223e7f_67.png', 'shoeId': 141985420321}], 'holes': [{'index': 0, 'type': 4, 'quality': 0, 'price': 1000, 'dataID': 0, 'gemId': 0, 'addv': 0, 'gAddv': 0, 'hAddv': 0}, {'index': 1, 'type': 4, 'quality': -1, 'price': 0, 'dataID': 0, 'gemId': 0, 'addv': 0, 'gAddv': 0, 'hAddv': 0}, {'index': 2, 'type': 1, 'quality': -1, 'price': 0, 'dataID': 0, 'gemId': 0, 'addv': 0, 'gAddv': 0, 'hAddv': 0}, {'index': 3, 'type': 4, 'quality': -1, 'price': 0, 'dataID': 0, 'gemId': 0, 'addv': 0, 'gAddv': 0, 'hAddv': 0}]}
        """
        url = self.creates_url_params(endpoint='orderdata', orderId=order_id, sessionID=self.sessionID)
        response = self.session.get(url)
        return response

    # @http_stepn_watcher
    # def get_buyprop(self, order_id):
    #     """ https://api.stepn.com/run/buyprop?orderID=40519097&price=10000000000 """
    #     pass

    @classmethod
    def creates_url_params(cls, endpoint, **kwargs) -> str:
        # Avoid rate limits
        time.sleep(1)

        url = f"{url_api}/{endpoint}?"

        for i, (key, value) in enumerate(kwargs.items()):
            if i > 0:
                url = f"{url}&"

            url = f"{url}{key}={value}"

        logs = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {url}\n"
        with open("log.txt", "a") as log_file:
            log_file.write(logs)

        print(logs)
        return url

    @classmethod
    def replace_binded_vars(cls, conditions, row):
        """Replace all the binding vars"""
        if not conditions or not row:
            return None

        while "%" in conditions:
            var_to_replace = conditions.split('%')[1].split()[0]
            conditions = conditions.replace(f"%{var_to_replace}", f"{row.get(var_to_replace)}")

        return conditions

    @staticmethod
    def get_orderdata_attrs(row, attr, default=0):
        index = mapping_response_attrs_reversed[attr]
        attrs = row.get('data').get('attrs')
        return attrs[index] if len(attrs) > 0 else default

    @classmethod
    def replace_detail_binded_vars(cls, conditions, row):
        """Replace all the binding vars for the data details"""
        while "%" in conditions:
            var_to_replace = conditions.split('%')[1].split()[0]

            if 'attr.' in var_to_replace:
                value = var_to_replace.split('attr.')[1]
                real_value = cls.get_orderdata_attrs(row, value)
            else:
                real_value = row.get(var_to_replace)

            conditions = conditions.replace(f"%{var_to_replace}", str(real_value))

        return conditions

    @staticmethod
    def reduce_item(details: dict):
        if 'sellPrice' in details:
            details['sellPrice'] = int(details['sellPrice']) / 1000000
        return details

    @staticmethod
    def human_readable_stats(title: str, chain: str, details: dict):
        url = f"{url_front}/order/{details.get('id')}"
        message = f"{title} => details: {details.get('sellPrice')} {chain} - lvl {details.get('level')} - " \
                  f"{mapping_quality_reversed[details.get('quality')]} - {details.get('mint')} mint"
        return f"{message}\nLink: {url}\n"
