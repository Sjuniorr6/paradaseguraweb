from django.db import models

# Create your models here.
class empresasModels(models.Model):
    empresa =[
        ('Pessao Fisica','Pessoa Fisica'),
        ('Pessoa Juridica','Pessoa Juridica')
    ]
    tipoempresa = models.CharField(max_length=50,null=True, blank=True)
    tipopessoa = models.CharField(choices=empresa,max_length=50,  null=True,blank=True)
    razaosocial = models.CharField(max_length=50,null=True,blank=True)
    nomefantasia = models.CharField(max_length=50,null=True,blank=True)
    cnpj = models.CharField(max_length=50,null=True,blank=True)
    def __str__(self):
        return self.nomefantasia or self.razaosocial or "Empresa sem nome"
    