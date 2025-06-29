# Configuração do Zoom G3X - RaspMIDI

## ⚠️ Requisitos Obrigatórios

### Alimentação
- **Fonte de alimentação 9V obrigatória**
- **NÃO funciona apenas via USB**
- Sem alimentação externa, o Zoom G3X não responde a comandos MIDI

### Conexões
- Cabo USB para conexão MIDI
- Fonte de alimentação 9V (incluída na caixa do Zoom G3X)

## 🔧 Configuração Passo a Passo

### 1. Conecte a Alimentação
```
1. Conecte a fonte de alimentação 9V ao Zoom G3X
2. Conecte a fonte na tomada
3. Ligue o Zoom G3X
```

### 2. Conecte o USB
```
1. Conecte o cabo USB do Zoom G3X ao computador/Raspberry Pi
2. Aguarde o sistema reconhecer o dispositivo
```

### 3. Configure no RaspMIDI
```
1. Acesse a interface web do RaspMIDI
2. Vá para a seção "Dispositivos MIDI"
3. Selecione "ZOOM G Series" como dispositivo de saída
4. Clique em "Salvar Configuração"
```

## 🚨 Problemas Comuns

### Dispositivo não responde
**Sintoma**: Comandos MIDI não funcionam
**Causa**: Alimentação apenas via USB
**Solução**: Conecte a fonte de alimentação 9V

### Dispositivo não aparece na lista
**Sintoma**: Zoom G3X não aparece nos dispositivos disponíveis
**Causa**: Driver não instalado ou dispositivo não reconhecido
**Solução**: 
1. Verifique se o cabo USB está bem conectado
2. Instale os drivers do Zoom G3X
3. Reinicie o sistema

### Comandos MIDI falham
**Sintoma**: Erro "Erro ao enviar Program Change"
**Causa**: Dispositivo não está respondendo
**Solução**:
1. Verifique se a alimentação externa está conectada
2. Use o botão "Testar Conexão" na interface
3. Verifique se o dispositivo correto está selecionado

## 🧪 Teste de Funcionamento

### 1. Teste Básico
```
1. Abra a interface web do RaspMIDI
2. Vá para "Comandos MIDI"
3. Clique em "Banco 1" ou "Banco 2"
4. O Zoom G3X deve mudar de patch
```

### 2. Teste de Efeitos
```
1. Vá para "Controle de Efeitos"
2. Ligue/desligue efeitos individuais
3. Os efeitos devem responder no Zoom G3X
```

### 3. Teste de Conexão
```
1. Clique em "Testar Conexão" na interface
2. O sistema deve confirmar que o dispositivo está respondendo
```

## 📋 Checklist de Verificação

- [ ] Fonte de alimentação 9V conectada
- [ ] Zoom G3X ligado
- [ ] Cabo USB conectado
- [ ] Dispositivo aparece na lista de dispositivos
- [ ] Zoom G3X selecionado como dispositivo de saída
- [ ] Teste de conexão passa
- [ ] Comandos MIDI funcionam

## 🔍 Diagnóstico

### Logs do Sistema
Verifique os logs em `logs/` para mensagens como:
- "Zoom G3X conectado na porta: ZOOM G Series"
- "PC enviado com sucesso para ZOOM G Series"

### Interface Web
- Status MIDI deve mostrar "Conectado"
- Dispositivos devem listar "ZOOM G Series"
- Alertas de alimentação devem aparecer se necessário

## 📞 Suporte

Se os problemas persistirem:
1. Verifique se a fonte de alimentação está funcionando
2. Teste o Zoom G3X com outro software MIDI
3. Verifique se o cabo USB não está danificado
4. Consulte a documentação oficial do Zoom G3X 