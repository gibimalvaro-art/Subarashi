# Subarashi: voz, vídeo e tela para a galera do Norte, sem servidor central

O Subarashi é uma **edição comunitária do Jami** (cliente de desktop
`jami-client-qt`, licença GNU GPLv3). Ele substitui a ideia anterior do Igarapé:
em vez de depender de um computador ou servidor central, cada computador conversa
direto com os outros, como o Jami.

*Subarashi (素晴らしい) é uma palavra japonesa que significa “maravilhoso”.*

## O que muda em relação ao Jami

| Área | Mudança |
|---|---|
| Nome | “Jami” virou “Subarashi” em todos os textos da interface, nas 121 traduções, na bandeja do sistema, nas notificações e nas pastas padrão de gravações e capturas de tela |
| Visual | Logo próprio (um rio em forma de “S”), ícones (Windows `.ico`, macOS `.icns`, Linux), animação de boas-vindas e cores trocadas do azul do Jami para verde-floresta |
| Português | Textos de boas-vindas voltados para a Região Norte; dica “O que significa Subarashi?” |
| Sobre | Linha de crédito: edição comunitária do Jami, usa a rede do Jami, não é produto oficial da Savoir-faire Linux. Os créditos e o copyright originais foram mantidos |
| Atualizador | **Desligado.** O atualizador do Jami baixaria o instalador oficial do Jami por cima do Subarashi |
| Doações | Faixa de campanha de doação do Jami desligada (os botões do “Sobre” continuam apontando para o Jami) |
| Windows | Executável `Subarashi.exe` |

**Não há bloqueio por CEP**, conforme combinado: num app sem servidor ele não
teria como ser imposto.

## O que precisa saber antes de usar

- **Não foi compilado nem testado por mim.** O ambiente onde trabalhei não tem o
  Qt 6.12 exigido pelo Jami, nem acesso aos servidores de onde a compilação baixa
  as dependências. Os arquivos de interface (QML) e as traduções foram checados
  quanto à sintaxe. A primeira compilação pode revelar ajustes.
- **É a mesma rede do Jami.** Quem usa Subarashi fala com quem usa Jami e
  vice-versa. Nomes de usuário são registrados no servidor de nomes do Jami.
- **“Sem servidor” tem nuance.** Não existe servidor central de vocês, e as
  mensagens e chamadas vão direto entre os computadores. Mas o Jami usa, por
  padrão, alguns servidores de apoio da Savoir-faire Linux: o nó de entrada da
  rede (DHT), o servidor de nomes e o retransmissor (TURN) para quando a conexão
  direta falha.
- **Chamadas em grupo:** o aparelho de quem criou o grupo hospeda a chamada. Se ele
  tiver internet fraca, a chamada sofre.
- **O que ainda se chama Jami por dentro:** o executável no Linux (`jami`), o
  identificador do app (`net.jami.Jami`), as pastas de dados e o protocolo
  `jami:`. Por isso **não instale o Jami e o Subarashi no mesmo computador**: eles
  compartilham as contas e as configurações do núcleo.
- **Marca:** o nome e o logo do Jami saíram da interface, mas confira a política de
  marca da Savoir-faire Linux antes de distribuir para o público.
- **Licença GPLv3:** ao entregar o programa a outras pessoas, o código-fonte
  (inclusive estas mudanças) precisa ir junto ou ficar disponível para elas.
- Celular: estas mudanças valem só para o desktop (Windows, Linux, macOS). Os apps
  de Android e iOS do Jami ficam em outros repositórios.

## Baixar o programa pronto (Windows)

No GitHub deste projeto: aba **Actions** > **Compilar Subarashi para Windows** >
**Run workflow**. Quando terminar, o `.zip` com o `Subarashi.exe` aparece na aba
**Releases**. Extraia numa pasta e abra o `Subarashi.exe`. O Windows pode avisar que
o programa é desconhecido (não tem assinatura digital): "Mais informações" >
"Executar assim mesmo".

## Como compilar no próprio computador

Resumo do `INSTALL.md` (leia o original para os detalhes). É demorado: o núcleo
do Jami compila dezenas de bibliotecas, e a primeira vez pode levar horas.

**Windows**
1. Instale o Visual Studio 2022 (C++), o Qt 6.12 (MSVC 64 bits, com os módulos
   listados no `INSTALL.md`), Python 3, Git, CMake e o WiX, se quiser instalador.
2. Num terminal do Visual Studio, dentro desta pasta:
   ```
   python build.py --dependencies
   python build.py --init --qt C:/Qt/6.12.0/msvc2022_64
   python build.py --install --qt C:/Qt/6.12.0/msvc2022_64
   ```

**Linux (Debian/Ubuntu)**
```
./build.py --init --qt=$HOME/Qt/6.12.0/gcc_64
sudo ./build.py --dependencies
./build.py --install --qt=$HOME/Qt/6.12.0/gcc_64
```

O `--init` baixa o núcleo (`daemon`) e as demais dependências pelo Git; por isso a
pasta `.git` está incluída.

## Atualizar com versões novas do Jami

Todas as mudanças estão num único commit. O arquivo `subarashi.patch` tem as
mudanças de código e texto; os arquivos de imagem estão em `resources/images/`.
Para trazer correções novas do Jami: `git pull` do repositório original e
reaplique o commit (`git cherry-pick`), resolvendo conflitos nas traduções, se
houver.

Origem: `https://github.com/savoirfairelinux/jami-client-qt`, commit `15eb82e`
(20/11/2026).
