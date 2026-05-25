# Unified Transcription Suite - Instruções

Este projeto unifica o Gravador de Áudio e os Transcritores (AssemblyAI e Deepgram) em uma única interface moderna.

## Instalação

1. **Dependências**: Certifique-se de que as bibliotecas necessárias estão instaladas.
   Execute no terminal:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configuração**:
   - Renomeie `.env.example` para `.env`.
   - Coloque suas chaves de API do AssemblyAI e Deepgram.

## Como Executar

Execute o arquivo `run_unified.bat` ou use o comando:
```bash
python main.py
```

## Funcionalidades

- **Aba Gravador**:
  - Seleção de microfone.
  - Gravação de áudio com contador de tempo e tamanho.
  - Salvamento automático na pasta configurada.

- **Aba Transcritor**:
  - Escolha entre AssemblyAI e Deepgram.
  - **Arraste e Solte** arquivos de áudio para transcrever.
  - Ou use o botão "Selecionar Arquivo".
  - Texto transcrito aparece na tela com opção de copiar.

## Notas

- O modo "Monitoramento de Pasta" foi substituído por "Arrastar e Soltar" para uma experiência mais interativa na interface unificada.
