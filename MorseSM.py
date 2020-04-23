from libdw import sm

#Input: 0->Dot, 1->Dash
class MorseSM(sm.SM):
    #Dictionary of traversal paths
    #Elem: 0->Dot, 1->Dash, 2->Return val to program
    fsmTree = {
                'Idle':['E','T','*'],       #Lv 0
                'E':['I','A','*'],          #Lv 1
                'T':['N','M','*'],
                'I':['S','U','*'],          #Lv 2
                'A':['R','W','*'],
                'N':['D','K','*'],
                'M':['G','O','*'],
                'S':['H','V','*'],          #Lv 3
                'U':['F','*','*'],
                'R':['L','*','*'],
                'W':['P','J','*'],
                'D':['B','X','*'],
                'K':['C','Y','*'],
                'G':['Z','Q','*'],
                'O':['*','*','*'],
                '*':['*','*','*']
                }

    def __init__(self):
        #Add level 4 items for remaining characters
        charToAdd = ['H','V','F','L','P','J','B','X','C','Y','Z','Q']
        for ch in charToAdd:
            self.fsmTree[ch] = ['*','*','*']
        self.start_state = 'Idle'

    def get_next_values(self, state, inp):
        if state in self.fsmTree:            #If state exist in dict
            charToReturn = self.fsmTree[state][int(inp)]
            #print(state,inp,self.fsmTree[state][int(inp)])
            if(charToReturn=='*'):
                if(inp=='0' or inp=='1'):
                    res = 'NA', 'NA'        #If both state = * and input is 1/2, return None (Invalid)
                else:
                    res = state, state        #Return state as result if it's *
            else:
                res = self.fsmTree[state][int(inp)], inp
        else:
            res = None, None
        return res

    def getCharacter(self, codeStr):
        if(len(codeStr)<6): #Accept only less than 5 numbers and numbers only
            if(codeStr.isdigit()):
                if(codeStr[-1]=="2"):
                    return MorseSM().transduce(codeStr)[-1]    #Return only last character
                else:
                    return 'Error: Missing back delimiter!'
            else:
                return 'Error: Not all char are digit(s)!'
        else:
            return 'Error: String length exceeded!'

    def testAllCharacters(self):
        res = []
        for i in range(5):
            for j in range(2**i):
                testCode = "%0*d2"%(i,int(bin(j)[2:]))       #Remove 1st 2 char, convert back to int
                res_char = MorseSM().transduce(testCode)[-1]
                print("%s: %s"%(testCode, res_char))
                res.append(res_char)
        return res

    def exceptionTest(self):                    #Test error catching
        res = ["010111","011@","011","01112"]
        for el in res:
            print('Test','Pass->' if len(gg.getCharacter(el))==1 else 'Fail->',gg.getCharacter(el))
