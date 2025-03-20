from django.db import models

# Create your models here.
from django.db import models
from geopy.distance import geodesic
from django.db import models

class Equipamento(models.Model):
    STATUS_CHOICES = [
        ("em_viagem", "Em Viagem"),
        ("no_destino", "No Destino"),
        ("desacoplado", "Desacoplado"),
        ("em_estoque", "Em Estoque"),
        ("na_fazenda", "Na Fazenda"),
    ]

    identificador = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="Identificador do Equipamento"
    )
    CCID = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="CCID"
    )
    data_entrega = models.DateField(
        verbose_name="Data de Entrega",
        null=True,
        blank=True
    )
    requisicao = models.CharField(
        max_length=100,
        verbose_name="Requisição"
    )
    cliente = models.CharField(
        max_length=150,
        verbose_name="Cliente"
    )
    local_entrega = models.CharField(
        max_length=200,
        verbose_name="Local de Entrega"
    )
    modelo = models.CharField(
        max_length=100,
        verbose_name="Modelo"
    )
    sla_insercao = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="SLA de Inserção"
    )
    sla_viagem = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="SLA de Viagem"
    )
    sla_retirada = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="SLA de Retirada"
    )
    sla_envio_brasil = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="SLA de Envio ao Brasil"
    )
    sla_operacao = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="SLA da Operação"
    )
    data_insercao = models.DateTimeField(
        verbose_name="Data de Inserção",
        null=True,
        blank=True
    )
    data_chegada_destino = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data de Chegada no Destino"
    )
    data_retirada = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data de Retirada"
    )
    data_envio_brasil = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data de Envio ao Brasil"
    )
    data_brasil = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data no Brasil"
    )
    BL = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="BL"
    )
    container = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Container"
    )
    status_operacao = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="em_viagem",
        verbose_name="Status da Operação"
    )
    reposicao = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Reposição"
    )
    observacao = models.TextField(
        null=True,
        blank=True,
        verbose_name="Observação"
    )
    latitude = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Latitude"
    )
    longitude = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Longitude"
    )
    # Ajuste o verbose_name do campo destino para algo que faça sentido (ex.: "Destino")
    destino = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="Destino"
    )

    #
    # -- CAMPOS NOVOS ABAIXO (de acordo com a sua tabela) --
    #

    # Se no banco a coluna está literalmente "Data / Embarque Maritimo",
    # você pode mapear assim:
    data_embarque_maritimo = models.CharField(max_length=50,
        db_column="Data_Embarque_Maritimo",
        null=True,
        blank=True,
        verbose_name="Data de Embarque Marítimo"
    )

    data_desembarque_maritimo = models.DateField(
        db_column="Data_Desembarque_Maritimo",
        null=True,
        blank=True,
        verbose_name="Data de Desembarque Marítimo"
    )

    sla_terrestre = models.IntegerField(
        db_column="SLA_Terrestre",
        null=True,
        blank=True,
        verbose_name="SLA Terrestre"
    )

    sla_maritimo = models.IntegerField(
        db_column="SLA_Maritimo",
        null=True,
        blank=True,
        verbose_name="SLA Marítimo"
    )

    # Se a coluna no banco for só "Local", mas você já usa 'local_entrega',
    # use outro nome de atributo em Python (por exemplo local_atual).
    local_atual = models.CharField(
        db_column="Local",
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Local"
    )

    status_do_container = models.CharField(
        db_column="Status_do_Container",
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Status do Container"
    )

    data_do_desembarque = models.DateField(
        db_column="Data_do_Desembarque",
        null=True,
        blank=True,
        verbose_name="Data do Desembarque"
    )

    # Se existir uma coluna "Data / Brasil" no banco e você quiser
    # diferenciá-la de data_brasil, crie um segundo campo, por exemplo:
    # data_brasil2 = models.DateField(
    #     db_column="Data / Brasil",
    #     null=True,
    #     blank=True,
    #     verbose_name="Data / Brasil"
    # )

    


    def __str__(self):
        return f"{self.identificador} - {self.modelo} ({self.cliente})"

    def atualizar_status_pela_localizacao(self):
        if self.latitude is None or self.longitude is None:
            self.status_operacao = "em_viagem"
            self.save()
            return

        # Defina as cercas com suas coordenadas e raio
        cercas = [
            {"nome": "Carmocoffe", "coordenadas": [-21.6319, -45.2740], "raio": 500, "cor": "red"},
            {"nome": "Alto Cafezal", "coordenadas": [-18.9484, -47.0058], "raio": 500, "cor": "red"},
            {"nome": "BOURBON SPECIALTY COFFEES", "coordenadas": [-21.7804, -46.5690], "raio": 500, "cor": "red"},
            {"nome": "COOXUPÉ", "coordenadas": [-21.2937, -46.7222], "raio": 500, "cor": "red"},
            {"nome": "EXPOCACCER", "coordenadas": [-18.9455, -47.0071], "raio": 500, "cor": "red"},
            {"nome": "NKG", "coordenadas": [-21.5771, -45.4721], "raio": 500, "cor": "red"},
            {"nome": "VELOSO COFFEE", "coordenadas": [-18.9981, -46.3011], "raio": 500, "cor": "red"},
            {"nome": "ANTUERPIA", "coordenadas": [51.2639, 4.41496], "raio": 5000, "cor": "green"},
            {"nome": "porto", "coordenadas": [51.3032, 4.2824], "raio": 8000, "cor": "green"},
            {"nome": "BREMEN", "coordenadas": [53.1208, 8.7345], "raio": 500, "cor": "green"},
            {"nome": "AVENCHES", "coordenadas": [46.8938, 7.0514], "raio": 5000, "cor": "green"},
            {"nome": "BREMENPORT", "coordenadas": [53.0584, 8.8966], "raio": 500, "cor": "green"},
            {"nome": "BREMENPORT2", "coordenadas": [53.1258, 8.7190], "raio": 6000, "cor": "green"},
            {"nome": "ROMONT", "coordenadas": [46.6806, 6.9051], "raio": 3000, "cor": "green"},
            {"nome": "BARCELONA", "coordenadas": [41.3504, 2.1635], "raio": 500, "cor": "green"},
            {"nome": "orbe", "coordenadas": [46.7266, 6.5365], "raio": 2500, "cor": "green"}
        ]

        # Calcula a distância e atualiza o status
        for cerca in cercas:
            distancia = geodesic(
                (self.latitude, self.longitude),
                (cerca["coordenadas"][0], cerca["coordenadas"][1])
            ).meters
            if distancia <= cerca["raio"]:
                if cerca["cor"] == "red":
                    self.status_operacao = "na_fazenda"
                elif cerca["cor"] == "green":
                    self.status_operacao = "no_destino"
                self.save()
                break
        else:
            self.status_operacao = "em_viagem"
            self.save()
