import requests,re
from mTransKey.transkey import mTransKey

class Cultureland:
    def __init__(self,id_,pw):
        self.s = requests.session()
        self.cookie=""
        self.id_=id_
        self.pw=pw

    def _islogin(self):
        resp=self.s.post("https://m.cultureland.co.kr/mmb/isLogin.json",headers={"Cookie":self.cookie})
        if resp.text!='true':
            return False
        else:
            return True

    def _login(self):
        if self._islogin():
            return True
        mtk = mTransKey(self.s, "https://m.cultureland.co.kr/transkeyServlet")
        pw_pad = mtk.new_keypad("qwerty", "passwd", "passwd")
        encrypted = pw_pad.encrypt_password(self.pw)
        hm = mtk.hmac_digest(encrypted.encode())
        resp = self.s.post("https://m.cultureland.co.kr/mmb/loginProcess.do",data={"agentUrl": "","returnUrl": "","keepLoginInfo": "","phoneForiOS": "","hidWebType": "other","userId": self.id_,"passwd": "*"*len(self.pw),"transkeyUuid": mtk.get_uuid(),"transkey_passwd": encrypted,"transkey_HM_passwd": hm})
        self.cookie=f"JSESSIONID={str(resp.cookies).split('JSESSIONID=')[1].split(' ')[0]}"
        if self._islogin():
            return True
        else:
            return False

    def get_balance(self):
        if not self._login():
            return (False,)
        resp=self.s.post("https://m.cultureland.co.kr/tgl/getBalance.json",headers={"Cookie":self.cookie})
        result=resp.json()
        if result['resultCode']!="0000":
            return False, result
        return True,int(result['blnAmt']),int(result['bnkAmt']) # (True, 사용가능, 보광중)

    def charge(self,pin):
        if not self._login():
            return (False,)
        pin=re.sub(r'[^0-9]', '', pin)
        if len(pin)!=16 and len(pin)!=18:
            return (False,)
        pin = [pin[i:i + 4] if i != 12 and len(pin)>12 else pin[i:] for i in range(0, 14, 4)]
        self.s.get('https://m.cultureland.co.kr/csh/cshGiftCard.do',headers={"Cookie":self.cookie})
        mtk = mTransKey(self.s, "https://m.cultureland.co.kr/transkeyServlet")
        pw_pad = mtk.new_keypad("number", "txtScr14", "scr14")
        encrypted = pw_pad.encrypt_password(pin[-1])
        hm = mtk.hmac_digest(encrypted.encode())
        hm_ = mtk.hmac_digest(b'')
        resp=self.s.post('https://m.cultureland.co.kr/csh/cshGiftCardProcess.do',headers={"Cookie":self.cookie},data={'scr11':pin[0],'scr12':pin[1],'scr13':pin[2],'scr14':'*'*len(pin[-1]),'scr21':"",'scr22':"",'scr23':"",'scr24':'','scr31':'','scr32':'','scr33':'','scr34':'','scr41':'','scr42':'','scr43':'','scr44':'','scr51':'','scr52':'','scr53':'','scr54':'','transkeyUuid':mtk.get_uuid(),'transkey_txtScr14':encrypted,'transkey_HM_txtScr14':hm,'transkey_txtScr24':'','transkey_HM_txtScr24':hm_,'transkey_txtScr34':'','transkey_HM_txtScr34':hm_,'transkey_txtScr44':'','transkey_HM_txtScr44':hm_,'transkey_txtScr54':'','transkey_HM_txtScr54':hm_})
        result=resp.text.split('<td><b>')[1].split("</b></td>")[0]
        if '충전 완료' in resp.text:
            return 1,int(resp.text.split("<dd>")[1].split("원")[0].replace(",",""))
        elif result in ['이미 등록된 문화상품권','상품권 번호 불일치']:
            return 0, result
        elif '등록제한(10번 등록실패)' in result:
            return 2,'등록제한'
        else:
            return 3,result

if __name__=="__main__":
    cl=Cultureland("ID","PW")
    print(cl.charge("PIN-CODE"))
    print(cl.get_balance())