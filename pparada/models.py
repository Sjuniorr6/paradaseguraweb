from django.db import models
from django.utils import timezone
class paradasegura(models.Model):
    EMBARCADOR_TIPO = [
        ('CORTEVA', 'CORTEVA'),
        ('BAYER', 'BAYER'),
        ('COMANDO LOG', 'COMANDO LOG'),
        ('OUTROS', 'OUTROS'),
    ]
   
    POSTOS_INFO1 = {
        '1': {
            'cadeados': [
                ('1017242', '1017242'),
                ('1017287', '1017287'),
                ('1016690', '1016690'),
                ('1017601', '1017601'),
                ('1017716', '1017716'),
            ],
            
            
            
            'iscas': [
                ('807613081', '807613081'),
                ('807612797', '807612797'),
                ('807612814', '807612814'),
                ('807548077', '807548077'),
                ('807587224', '807587224'),
            ],
        },
        '2': {
            'cadeados': [
                ('1017692', '1017692'),
                ('1017132', '1017132'),
                ('1018072', '1018072'),
                ('1016895', '1016895'),
                ('1017935', '1017935'),
            ],
            'iscas': [
                ('807612587', '807612587'),
                ('807587474', '807587474'),
                ('807612614', '807612614'),
                ('807612614', '807612614'),
                ('807587471', '807587471'),
            ],
        },
        '3': {
            'cadeados': [
                ('1017977', '1017977'),
                ('1018035', '1018035'),
                ('1017246', '1017246'),
                ('1017972', '1017972'),
                ('1017819', '1017819'),
            ],
            'iscas': [
                ('807612727', '807612727'),
                ('807558802', '807558802'),
                ('807612819', '807612819'),
                ('807558824', '807558824'),
                ('807613823', '807613823'),
            ],
        },
        '4': {
            'cadeados': [
                ('1016679', '1016679'),
                ('1017927', '1017927'),
                ('1017961', '1017961'),
                ('1017614', '1017614'),
                ('1018144', '1018144'),
            ],
            'iscas': [
                ('807612611', '807612611'),
                ('807587594', '807587594'),
                ('807612586', '807612586'),
                ('807587570', '807587570'),
                ('807612716', '807612716'),
            ],
        },
        '5': {
            'cadeados': [
                ('1017994', '1017994'),
                ('1017702', '1017702'),
                ('1017274', '1017274'),
                ('1018134', '1018134'),
                ('1017649', '1017649'),
            ],
            'iscas': [
                ('807558949', '807558949'),
                ('807296832', '807296832'),
                ('807612622', '807612622'),
                ('807613796', '807613796'),
                ('807296849', '807296849'),
            ],
        },
        '6': {
            'cadeados': [
                ('1018057', '1018057'),
                ('1017084', '1017084'),
                ('1017685', '1017685'),
                ('1017695', '1017695'),
                ('1017971', '1017971'),
            ],
            'iscas': [
                ('807587475', '807587475'),
                ('807612823', '807612823'),
                ('807578510', '807578510'),
                ('807612584', '807612584'),
                ('807613790', '807613790'),
            ],
        },
        '7': {
            'cadeados': [
                ('1017812', '1017812'),
                ('1017967', '1017967'),
                ('1017759', '1017759'),
                ('1017214', '1017214'),
                ('1017663', '1017663'),
            ],
            'iscas': [
                ('807613824', '807613824'),
                ('807558953', '807558953'),
                ('807296838', '807296838'),
                ('807612713', '807612713'),
                ('807612701', '807612701'),
            ],
        },
    }

    POSTO = [
        ('0', '---'),
        ('1', 'POSTO DA SERRA'),
        ('2', 'POSTO BURITIZINHO'),
        ('3', 'POSTO BRASILEIRÃO'),
        ('4', 'POSTO TREVÃO'),
        ('5', 'POSTO JN'),
        ('6', 'POSTO CAPIXABOM'),
        ('7', 'POSTO GRAAL RUBI'),
    ]
    parada = [
        ('Pernoite', 'Pernoite'),
        ('Refeição', 'Refeição'),
        ('Check List', 'Check List'),
        
    ]
    projeto = [
        ('SIM', 'SIM'),
        ('NÃO', 'NAO'),
       
        
    ]

    inconforme = [
        ('NÃO', 'NÃO'),
        ('SENSOR PORTA MOTORISTA', 'SENSOR PORTA MOTORISTA'),
        ('SENSOR PORTA PASSAGEIRO', 'SENSOR PORTA PASSAGEIRO'),
        ('TECLADO', 'TECLADO'),
        ('BOTÃO DE PÂNICO', 'BOTÃO DE PÂNICO'),
        ('LACRE BAÚ', 'LACRE BAÚ'),
        ('SIRENE', 'SIRENE'),
        ('BLOQUEIO', 'BLOQUEIO'),
        ('CHAVE GERAL', 'CHAVE GERAL'),
        ('CNH', 'CNH'),
        ('DOCUMENTO DO VEÍCULO', 'DOCUMENTO DO VEÍCULO'),
        ('DOCUMENTO DA CARRETA', 'DOCUMENTO DA CARRETA'),
        ('OUTROS', 'OUTROS'),
    ]
    POSTOS_INFO2 = {
        '1': {
            'pa': [
                ('1', 'Fabiane'),
                ('2', 'Gustavo'),
                ('3 ', 'Pamela '),
                ('4', 'Larissa'),
               
           
            ],
        },
        '2': {
            'pa': [
                ('1', 'Deny'),
                ('2', 'Herick'),
                ('3', 'Heliene'),
                ('4', 'Jéssica'),
               
           
            ],
        },
        '3': {
            'pa': [
                ('1', 'Matheus Lucas'),
                ('2', 'Hiago Martins'),
                ('3', 'Lorrane Lemos'),
                ('3', 'Valterson Viana'),
               
            ],
            
        },
        '4': {
            'pa': [
                ('1', 'Zildo'),
                ('2', 'Felipe'),
                ('3', 'Licinio'),
                ('4', 'Rone'),
                
            ],
           
        },
        '5': {
            'pa': [
                ('1', 'João'),
                ('2', 'Keven'),
                ('3', 'Weslei'),
                ('4', 'Robson'),
               
            ],
           
        },
        '6': {
            'pa': [
                ('1', 'Thiago'),
                ('2', 'Nicoly'),
                ('3', 'Davidson'),
                ('4', 'Robson'),
                
            ],
           
        },
        '7': {
            'pa': [
                ('1', 'Lucas Euzébio'),
                ('2 ', 'Eduardo '),
                ('3', 'Josielin'),
                ('4', 'Luiz Henrique'),
                
            ],
            
        },
    }
    nome_do_pa = models.CharField(max_length=255, blank=True, null=True)
    data_criacao = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    embarcador = models.CharField(choices=EMBARCADOR_TIPO, max_length=255, blank=True, null=True)
    transportador = models.CharField(max_length=255, blank=True, null=True)
    placa_cavalo = models.CharField(max_length=255, blank=True, null=True)
    foto_cavalo = models.ImageField(upload_to='fotos_cavalo/', blank=True, null=True)
    foto_documento_cavalo = models.ImageField(upload_to='fotos_documento_cavalo/', blank=True, null=True)
    placa_carreta = models.CharField(max_length=255, blank=True, null=True)
    foto_carreta = models.ImageField(upload_to='fotos_carreta/', blank=True, null=True)
    foto_carreta_documento = models.ImageField(upload_to='fotos_carreta_documento/', blank=True, null=True)
    nome_motorista = models.CharField(max_length=255, blank=True, null=True)
    cnh = models.ImageField(upload_to='fotos_motorista_documento/', blank=True, null=True)
    tipo_posto = models.CharField(choices=POSTO, max_length=255, blank=True, null=True)
    descreva = models.CharField(max_length=255, blank=True, null=True)
    id_rastreador = models.CharField(max_length=255, blank=True, null=True)
    id_cadeado = models.CharField(max_length=255, blank=True, null=True)
    tipo_parada = models.CharField(choices=parada,max_length=255, blank=True, null=True)
    status = models.CharField(default='AGUARDANDO', null=True, blank=True, max_length=50)
    saida = models.DateTimeField(blank=True, null=True)
    ciente_do_projeto = models.CharField(choices=projeto,max_length=50, null=True,blank=True )
    outros_embarcador = models.CharField(max_length=255, blank=True, null=True)

    
    
    previsao_saida = models.CharField(max_length=255, blank=True, null=True)
    previsao_de_saida = models.CharField(max_length=255, blank=True, null=True)
    Horario_de_saida = models.CharField(max_length=255, blank=True, null=True)
    inconformidade = models.CharField(choices=inconforme, max_length=255, blank=True, null=True)

    def save(self, *args, **kwargs):
        # Atualiza o campo 'saida' apenas quando o status for alterado para 'EM VIAGEM'
        if self.status == 'EM VIAGEM' and not self.saida:
            self.saida = timezone.now()
        super(paradasegura, self).save(*args, **kwargs)

    def __str__(self):
        return f"ticket {self.id} - {self.nome_motorista}"




class passagemmodel(models.Model):
    confome = [
        ('Não Confome','Não Confome'),
        ('Confome','Confome'),
     

  ]
    POSTO = [
        ('---', '---'),
        ('1', 'POSTO DA SERRA'),
        ('2', 'POSTO BURITIZINHO'),
        ('3', 'POSTO BRASILEIRÃO'),
        ('4', 'POSTO TREVÃO'),
        ('5', 'POSTO JN'),
        ('6', 'POSTO CAPIXABOM'),
        ('7', 'POSTO GRAAL RUBI'),
    ]
    Turnos = [
        ('Dia','Dia'),
        ('Noite','Noite'),
     

  ]
    POSTOS_INFO2 = {
        '1': {
            'pa': [
                ('1', 'Fabiane'),
                ('2', 'Gustavo'),
                ('3 ', 'Oliver '),
                ('4', 'Larissa'),
               
           
            ],
        },
        '2': {
            'pa': [
                ('1', 'Claudinei'),
                ('2', 'Herick'),
                ('3', 'Heliene'),
                ('4', 'Jéssica'),
               
           
            ],
        },
        '3': {
            'pa': [
                ('1', 'Valterson'),
                ('2', 'Ademir'),
                ('3', 'Wesley'),
               
            ],
            
        },
        '4': {
            'pa': [
                ('1', 'Rafael'),
                ('2', 'Felipe'),
                ('3', 'Patrícia'),
                ('4', 'Rone'),
                
            ],
           
        },
        '5': {
            'pa': [
                ('1', 'João'),
                ('2', 'Daniely'),
                ('3', 'Talia'),
                ('4', 'Robson'),
               
            ],
           
        },
        '6': {
            'pa': [
                ('1', 'Davidson'),
                ('2', 'Luiz Gustavo'),
                ('3', 'Nicoly'),
                ('4', 'Claudemir'),
                
            ],
           
        },
        '7': {
            'pa': [
                ('1', 'Silvio'),
                ('2 ', 'Eduardo '),
                ('3', 'Josielin'),
                ('4', 'Luiz Henrique'),
                
            ],
            
        },
    }
    nome_do_pa = models.CharField(max_length=255, blank=True, null=True)
    nome_do_posto = models.CharField(choices=POSTO,max_length=255, blank=True, null=True)
    turno = models.CharField(choices=Turnos,max_length=255, blank=True, null=True)
    data_criacao = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    Iscas = models.CharField(choices=confome, max_length=255, blank=True, null=True)
    notebook = models.CharField(choices=confome, max_length=255, blank=True, null=True)
    celular = models.CharField(choices=confome, max_length=255, blank=True, null=True)
    antena = models.CharField(choices=confome, max_length=255, blank=True, null=True)
    bodycam = models.CharField(choices=confome, max_length=255, blank=True, null=True)
    cadeados = models.CharField(choices=confome, max_length=255, blank=True, null=True)
    drone = models.CharField(choices=confome, max_length=255, blank=True, null=True)
    descrição = models.CharField(choices=confome, max_length=255, blank=True, null=True)
    fotos = models.ImageField(upload_to='imagens/', null=True, blank=True)
    


    def __str__(self):
        return self.data_criacao, self.nome_do_pa, self.nome_do_posto 

class paradasegura_ponto(models.Model):
    fotos = models.ImageField(upload_to='ponto/', null=True, blank=True)
    data_criacao = models.DateTimeField(auto_now_add=True, blank=True, null=True)