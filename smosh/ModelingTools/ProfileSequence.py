import re

class ProfileSequence():
    def __init__(self, estrutura):
        self.estrutura = estrutura
        # Correção 1: Converter o iterador de filter() para uma lista
        # Uma alternativa mais "pythônica" para remover strings vazias é uma list comprehension:
        # self.estruturaparticionada = [item for item in re.split(" ", self.estrutura) if item]
        self.estruturaparticionada = list(filter(None, re.split(" ", self.estrutura)))
        
    def __str__(self):
        # Correção 2: __str__ deve retornar uma string.
        # Garante que o índice 10 existe antes de tentar acessá-lo e convertê-lo.
        if len(self.estruturaparticionada) > 10:
            return str(float(self.estruturaparticionada[10]))
        else:
            return "Erro: Índice 10 não existe na estrutura particionada." # Ou outra mensagem de erro/valor padrão
            
    def name(self):
        # Adicionar verificações de limite para evitar IndexError
        if len(self.estruturaparticionada) > 1:
            return self.estruturaparticionada[1]
        return None # Ou levantar um erro
            
    def type(self):
        if len(self.estruturaparticionada) > 2:
            return self.estruturaparticionada[2]
        return None
            
    def startofStructure(self):
        if len(self.estruturaparticionada) > 5:
            return self.estruturaparticionada[5]
        return None
            
    def endofStructure(self):
        if len(self.estruturaparticionada) > 6:
            return self.estruturaparticionada[6]
        return None
            
    def sequenceSize(self):
        if len(self.estruturaparticionada) > 9:
            return self.estruturaparticionada[9]
        return None
            
    def identity(self):
        if len(self.estruturaparticionada) > 10:
            return self.estruturaparticionada[10]
        return None
            
    def sequence(self):
        if len(self.estruturaparticionada) > 12:
            return self.estruturaparticionada[12]
        return None
            
    def proteinName(self):
        # Garante que name() retorna algo antes de tentar fatiar
        name_val = self.name()
        if name_val is not None and len(name_val) >= 4:
            return name_val[:4]
        return None # Ou um valor padrão/erro
