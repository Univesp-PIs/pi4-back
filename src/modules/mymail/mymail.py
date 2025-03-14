import os
import smtplib
from email import encoders
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart

class MyMail:
        
    def __init__(self):

        # Variaveis gerais
        self.status = False
        self.sucesso = f'SUCESSO - {__name__}'
        self.falha = f'FALHA - {__name__}'
        self.erro = f'ERRO - {__name__}'

        # Variaveis especificas
        self.resultado = None
        self.lista_resultado = None

    # Configuração do servidor SMTP do Gmail
    def mail(self, type, login, password, recipient, head, body, path = None, file = None):

        """
        Função para enviar um e-mail podendo conter um ou mais documentos em anexos.

        Args:
            type (str): Tipo de e-mail ('gmail', 'outlook', etc.)
            login (str): Nome e sobrenome do usuário com e-mail.
            password (str): Senha do e-mail que irá enviar a mensagem.
            recipient (str/list): E-mail completo de um ou mais destinatarios.
            head (str): Supertitulo que deseja adicionar no e-mail.
            body (str): Mensagem que deseja escrever no e-mail.
            path (str/list, opcional): Caminho(s) para o(s) arquivo(s) que deseja anexar no corpo do e-mail.
                Padrão é 'None'.
            file (str/list, opcional): Nome(s) do(s) arquivo(s) que deseja anexar.
                Padrão é 'None'.
        """

        # Variaveis
        recipient_list = isinstance(recipient, list)
        path_list = isinstance(path, list)
        arquivo_list = isinstance(file, list)

        # TryCtach
        try:

            # Verificar as possiveis listas
            if recipient_list:

                # Atualizar o valor da variavel
                recipients = recipient

            else:

                # Criar uma lista unica
                recipients = [recipient]

            # Verificar as possiveis listas
            if path is None or path_list:

                # Atualizar o valor da variavel
                paths = path

            else:

                # Criar uma lista unica
                paths = [path]

            # Verificar as possiveis listas
            if file is None or arquivo_list:

                # Atualizar o valor da variavel
                arquivos = file

            else:

                # Criar uma lista unica
                arquivos = [file]

            # Retornar o valor das credenciais
            smtp_username = login
            smtp_password = password
            smtp_type = type

            # Configurar servidor SMTP
            #smtp_server = 'smtp.gmail.com'

            # Configurar porta SMTP
            #smtp_port = 587

            # Configurações do servidor SMTP com base no tipo de e-mail

            # Gmail server
            if smtp_type == 'gmail':
                smtp_server = 'smtp.gmail.com'
                smtp_port = 587

            # Outlook server
            elif smtp_type == 'outlook':
                smtp_server = 'smtp.office365.com'
                smtp_port = 587
                
            else:
                return {'status': False, 'error': 'Tipo de e-mail não suportado.'}

            # Criar mensagem
            message = MIMEMultipart()
            message['From'] = smtp_username
            message['To'] = ', '.join(recipients)
            message ['Subject'] = head

            # Adicionar o corpo do e-mail
            message.attach(MIMEText(body, 'plain'))

            # Criar lista rezada de valores
            attachment_path = []
            attachment_name = []

            # Configurar arquivos anexos
            if paths is not None:

                for valor in paths:

                    if arquivos is not None:

                        for name in arquivos:

                            # Caminho do arquivo anexo
                            arquivo_path = os.path.join(valor, name)

                            # Obter o nome do arquivo do caminho
                            arquivo_name = name

                            # Atulizar lista de resultados
                            attachment_path.append(arquivo_path)
                            attachment_name.append(arquivo_name)

                    else:

                        # Caminho do arquivo anexo
                        arquivo_path = valor

                        # Obter o nome do arquivo do caminho
                        arquivo_name = os.path.basename(arquivo_path)

                        # Atulizar lista de resultados
                        attachment_path.append(arquivo_path)
                        attachment_name.append(arquivo_name)

                for count in range(len(attachment_path)):

                    # Configurar arquivo para anexar ao e-mail
                    with open(attachment_path[count], 'rb') as attachment:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(attachment.read())
                        encoders.encode_base64(part)
                        part.add_header(
                            'content-disposition',
                            f'attachment; filename = {attachment_name[count]}'
                        )
                        message.attach(part)

            # Iniciar conexão com o servidor SMTP
            with smtplib.SMTP(smtp_server, smtp_port) as server:

                # Estabelecer conexão segura
                server.starttls()

                # Faezr login no servidor SMTP
                server.login(smtp_username, smtp_password)

                # Emviar e-mail
                server.sendmail(smtp_username, recipients, message.as_string())

                self.status = True
                print(self.sucesso)
                print('E-mail encaminhado com sucesso!')
                
        except Exception as aviso:
            self.status = False
            print(self.erro)
            print(aviso)

            # Retorne o erro como parte do dicionário de resultado
            return {'status': self.status, 'error': str(aviso)}  # Adicione isso

        return{'status': self.status}