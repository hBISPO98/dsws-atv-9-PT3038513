# E-mail 2 📧​

Evolução da aplicação web em Flask focada na integração de um sistema de notificações por e-mail (via Mailgun), incluindo campos de opt-in (checkbox) no formulário, gestão unificada de cadastros e atualizações de cargos com templates HTML dinâmicos.

---

## 🚀 O que mudou? (Versão Anterior vs. Versão Atual)

- **Notificações Automatizadas e Dinâmicas:** Integração com o Mailgun para disparar mensagens mediante evento — seja para notificar um novo registro ou avisar sobre a atualização de cargo de um utilizador existente.


- **Templates de E-mail Unificados:** Substituição do modelo estático por um template flexível (`user_update.html`) localizado na subpasta `mail/`.


- **Controle de Envio por Checkbox:** Presença da opção interativa no formulário (`BooleanField`) para que o utilizador decida se deseja ou não disparar o e-mail de notificação para o administrador.

---

## ⚙️ O que foi necessário implementar?

- **Configuração da API de Envio:** Implementação de tratamentos de exceção e formatação correta de destinatários (conversão de listas em strings separadas por vírgulas exigida pelo Mailgun).


- **Gestão de Cargos e Eventos:** Lógica de backend para distinguir se o envio ocorre por um novo cadastro (`is_new`) ou por uma alteração de função num registro já existente.


- **Refatoração do Template HTML:** Atualização do layout de e-mail utilizando condições do Jinja (`{% if is_new %}`) para alternar a mensagem exibida.

---

## 💡 Dicas de Boas Práticas Adotadas

- **Organização de Templates em Subpastas:** Manter os layouts de e-mail agrupados na pasta `mail/` melhora a legibilidade e a manutenção do projeto.


- **Modularização do Código:** Manter a função de envio isolada e segura (`try-except`) evita que falhas na API de e-mail derrubem a aplicação principal.

---

## 👩🏽‍💻 Demonstração
<div align="center">

| Interface Inicial - Inserção da Admin Jenny |
| :---: |
| <img src="https://github.com/user-attachments/assets/a90cbe4b-ceb1-48ab-89ee-6572985407ab" /> |

<br>

| Notificação de novo usuário cadastrado |
| :---: |
| <img src="https://github.com/user-attachments/assets/fdcd90e3-526c-465b-a34b-5683be984063" /> |

<br>

| Notificação da atualização de cadastro de usuário existente |
| :---: |
| <img src="https://github.com/user-attachments/assets/900d082a-d1d2-41d3-b555-d175d7696131" /> |

</div>
