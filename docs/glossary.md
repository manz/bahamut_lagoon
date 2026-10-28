# Glossary

The French terms the translation uses, and the rules that name spells. A new or changed name follows this page;
a change to a rule changes every name it covers.

## Abbreviations

| Term | FR | Not |
|---|---|---|
| HP | PV | HP |
| MP | PM | MP |
| Level | Nv | Lv |
| Experience | Expérience, Exp. only where it can't fit | XP |

Battle messages spell words out whenever they fit their line (`utils/battle_messages.py` checks the 30 bytes).
The status and equipment screens still abbreviate stats (Att., Déf., Vit., Mag., Intel., Mutat., Affin.).

## Elements

Each element has one word in descriptions and one qualifier in names. A spell's name uses its effect's element,
as its description states it, when the JP word says something else.

| JP | Element (descriptions) | Qualifier (names) |
|---|---|---|
| フレイム | Feu | de feu |
| アイス | Eau | de glace |
| サンダ- | Foudre | de foudre |
| ポイズン | Poison | toxique |
| ドラッグ | Absorbe-PV | vampire |
| ア-ス | Terre | de terre |
| セイント | Sacrée | sacré, sacrée |
| ダ-ク, あんこく | Ténèbres | noir, noire |
| うにうに | Neutre | uniuni (Uni- in a contraction) |
| ? | Neutre | ? |

The dragon screen's affinities (Feu, Eau, Foudre, Soin, Poison) are a dragon's stats, not elements: its Soin is
healing.

## Characters

`text/fr/names.xml` is the source: the prose writes a character as names.xml spells it, and the build encodes that
spelling as the name's reference (F4 and its index), so the script prints the record, or the name the player chose.
A name longer than its 8-code record (Frederica, Anastasia, Ekaterina, Fils de Zora) stays spelled out. A speaker
label is never in capitals and opens the speech's first line: "Matelite: Bien !", not "MATELITE:" alone on its line.

| JP | FR | Not |
|---|---|---|
| ビュウ | Byuu | |
| ヨヨ | Yoyo | |
| サラマンダー | Salamand (named by the player) | SALAMAND |
| ファーレンハイト | Fareneit (named by the player) | Farenheit, FARENHEIT |
| パルパレオス | Palparos | Palpaleos |
| マテライト | Matelite | Matelight |
| センダック | Sendak | Sendack |
| ビッケバッケ | Bikebake | Bikkebakke |
| トゥルース | Truth | Taurus, Truce |
| タイチョー | Taicho | Commandant |
| グンソー | Gunso | Sergent |
| バルクレイ | Barclay | Bareck |
| ドンファン | Donfan | Don Juan |
| ネルボ | Nerbo | Nelbo |
| ルキア | Ruki | Lukia |
| メロディア | Melody | Melodia, Mélodia |
| フレデリカ | Frederica | Frederika |
| モルテン | Morten | Molten |
| サウザー | Sauzer | |
| セリーヌ | Céline | CELINE |
| ドラゴンおやじ | Père Dragon | Docteur Dragon |
| レスタット | Lestat | Restatto |
| ペルソナ | Persona | Pelsona |
| グドルフ | Gudolf | Gudruff |

## Holy Dragons

| JP | FR | Not |
|---|---|---|
| 神竜 | Dragon Sacré, Dragons Sacrés | dragon |
| ヴァリトラ | Vritra | Valitra |
| リヴァイアサン | Léviathan | Leviathan |
| ヨルムンガンド | Jormungand | |
| ガルーダ | Garuda | |
| アレキサンダー | Alexandre | |

## Places and factions

| JP | FR | Not |
|---|---|---|
| カーナ | Kana | Kahna |
| キャンベル | Campbell | |
| マハール | Mahal | |
| グランベロス | Granbelos | |
| オレルス | Orelus | |
| 帝国 | l'Empire | |
| 戦竜隊 | l'Escadron Dragon | Cavalerie |
| 女王 | reine | Impératrice |
| 約束の地 | la Terre promise | la Place Promise |
| ゴドランド | Godland | Godrand |
| テード | Tedd | Teid |
| 反乱軍 | les Rebelles, l'armée rebelle | la Résistance |

## Game words

Item and class names in the dialog are written as items.xml and classes.xml spell them, in their case, accents
included: Remède, not DROGUE; Dragonnier, not Dragoon; Croisé, not Chevalier Croix; Diablotin, not Petit Démon.

| JP | FR | Not |
|---|---|---|
| ピロー | Piro | GP, Po |
| ターン | Tour | |
| フェイズ | Phase | Tour |
| パーティー | Escouade | Équipe, groupe |
| じょうほう (menu) | Inventaire | Infos |
| そうびしているかず | Équipés (next to Possédés) | NOMBRE EQUIPE |
| セーブ | Sauvegarder | Sauver |
| データがありません | Aucune donnée | PAS DE DONNEES |
| そうびなし | Aucun | NO ITEM |
| したしさ | Affin. | Joie |

## Set phrases

A JP formula takes what a French speaker says in that situation, not its dictionary words. The Not column is the
calque the stiffness review found in the script.

| JP | FR | Not |
|---|---|---|
| ごくろうさま, おつかれさま | Beau travail ; Tu dois être épuisé ; Au rapport ; a greeting | tu as bien travaillé, merci pour ta peine |
| はじめまして + よろしく | Enchanté, once | Enchanté… Ravi de te connaître |
| よろしく (introducing someone) | Voici… | faites bon accueil à |
| お世話になって | merci pour tout | vous êtes toujours si bon avec moi |
| とつぜんですが | sans crier gare ; a letter: Nous avons la joie de vous annoncer | c'est soudain, mais |
| どうぞ, どうぞどうぞ | Entrez donc ; Mais bien sûr ! | Je t'en prie, je t'en prie |
| なつかしい | Ça fait si longtemps ! | Ça me rappelle tant de souvenirs |
| たいしたもんだ | Chapeau ! ; Quelle allure ! | ils ne sont pas rien |
| たいへん(だ)! | Malheur ! ; Alerte ! | C'est grave ! |
| ふくざつ | Je ne sais plus que penser | sentiments partagés |
| むりもない | Ça se comprend | Je te comprends |
| しかたない | C'est comme ça | Tant pis |
| さすが | Digne de… | Bravo, on voit bien… |
| てれる | Tu me fais rougir ; J'en rougis | Tu me gênes, Que c'est gênant |
| ただいま | Je suis rentré | Me voici |
| 大切な人 | cher, qui compte | précieux |
| 人として…さいてい | le dernier des hommes, minable | en tant qu'être humain, le pire |
| さあ (answering a question) | Qui sait... | Allons... |
| って, んだって | il paraît, paraît-il, on dit que, or nothing, varied | à ce qu'il paraît on every line |
| この人, その人, あの方 | il, elle ; ce monsieur | cette personne |
| このドンファン, このメロディア | le grand Donfan ; ma petite Melody | ce Donfan, cette Melody |
| これで | Voilà… | Avec ça |
| ここは (leave it to) | Laissons faire… | Ici, on laisse faire |
| フッ, フフッ (smug) | Hé..., Héhé... | Hmph |
| 〜に伝わる (a legend) | une vieille légende de… | transmise à |
| 神竜の心を知る | découvrir, connaître le cœur des Dragons Sacrés | apprendre le cœur |
| 人間のむすめ | jeune humaine | fille humaine |
| 戦いの旅 | notre campagne, notre périple | le voyage du combat |
| 自由革命 | la révolution, la révolution pour la liberté | la révolution de la liberté |
| 帝国皇帝 | l'Empereur de Granbelos | Empereur de l'Empire Granbelos |

## Style

- **French word order.** The topic doesn't open the sentence on its own (« Les Dragons Sacrés veulent savoir ce qui
  est arrivé à Altair », not « Ce qui est arrivé à Altair... Les Dragons Sacrés veulent le savoir »), and an action
  is a verb, not a noun (« On part sauver la princesse ! », not « L'opération de sauvetage… commence »).
- **Pronouns after the first mention.** JP repeats a noun for want of pronouns; French names it once a speech, then
  says il, elle, eux or leur (0077 0x875 named the hommes-dragons three times and the Dragons Sacrés six).
- **Plain words.** A rare or literary word stands out in plain dialogue even when it's right (« fourbu », « il me
  tarde », « aux aguets »): say épuisé, j'ai hâte, si c'est toi qui veilles. Keep the bookish turn for the speaker it
  characterises (Matelite's drills, Zora's « qui l'eût cru », Donfan's grand phrases before « …enfin, je crois »).
- **Register by speaker.** Rush, Ruki, Bikebake and the crew say « on » and ask without inversion (« Tu es amoureux
  de quelqu'un ? »); inversion and « nous » belong to Matelite's set speeches, the royals and the Holy Dragons.

## Typography

- **Ellipses and exclamations.** A pause is one « ... », never « mais... ...Je »; a run of them is only silence
  (« ... ... ... ») or a countdown (0015). « !! » for a shout, a single « ! » in a calm line.
- **Hmph** is ふん (Matelite's grumble), not a smug フッ.
- **œ** is the ligature, Œ its capital (codes 0x99 and 0x9A, drawn in both the dialogue and the 8x8 font): cœur,
  œil, sœur, vœu, Œil-de-bœuf. Names transcribed from German keep oe (Stoessel, Mosskoenig).
- **Signs.** ( ) / ~ are drawn in the dialogue font; * is not, so no *stage directions*: say it (« Oh, je
  rougis... »). utils/tests/test_script_encoding.py fails on a character without a code or a glyph.

## Open questions, decided

Each question the review left open, with its decision. The pros and cons were argued with a second reviewer
against the JP text; the reason kept is the one that decided it.

- パーティー: Équipe in the menus, groupe in battle messages. **Decision: Escouade everywhere.** One game object,
  one word; Équipe sat next to Équiper and Équipés on the same screens. Fits: 40 px in the 7-cell battle command,
  « Expérience d'escouade : » 30 of 30 bytes, « Escouades triées » 74 px.
- クロスナイト (class) and クルーセイダー (dragon) were both Croisé. **Decision: the class keeps Croisé, the dragon is
  Templier.** The class is in the dialog and the status screen; the dragon is one row of dragons.xml.
- Names. **Decision: Godland, Tedd, Lestat, Persona, Gudolf; Dafira stays.** A katakana that renders a real name or
  word takes that spelling (Lestat is Anne Rice's, Persona a word, enemies.xml already said Gudolf); a coinage
  keeps what the text had.
- 反乱軍: Rebelles or Résistance. **Decision: les Rebelles (l'armée rebelle where 軍 matters).** Matelite (0020
  0x226–0x241) takes the insult as the group's name, which Résistance turns noble; Résistance came from DeJap.
- The dragon screen's STR, VIT, DEX, MIND, EXP, NEXT. **Decision: For., Endu., Adr., Esprit, Exp.:, Suiv.:**, each
  field given its JP cell count. HP, MP and LV are already French; VIT would read as Vit. (speed).
- Tu or vous. **Decision: vous for さま, どの, 姫, 隊長, or さん with です/ます; tu for a bare name, おまえ, きさま, あんた;
  vous for several people.** The pairs:
  - the knights to Yoyo: vous; Yoyo to them: tu. Byuu and Yoyo: tu both ways.
  - Byuu and the crew and knights (Matelite, Sendak, Rush, Bikebake, Donfan, Ruki, Melody, Zora, Hornet, Père
    Dragon): tu. Taicho to Byuu: tu (でアリマス is his tic, used on his own subordinate too; no « mon capitaine »).
  - Gunso, Barclay, Nerbo, Frederica, Ekaterina to Byuu: vous (さん, honorific verbs); Byuu to them: tu.
  - Truth to Byuu and to Matelite: vous; Matelite to Truth: tu. Taicho to Matelite: vous (どの); Matelite to Taicho:
    tu. Gunso to Taicho: vous; Taicho to Gunso: tu.
  - Palparos and Sauzer: tu. Palparos to Byuu: tu. Palparos and Yoyo: tu in private; vous where his JP turns to
    keigo in public (王女, ください: 0035 0x49e) and in the 0066 church flashback until « cessez de m'appeler
    princesse », and in her captivity (0075). Sauzer to Yoyo: vous. Matelite to Palparos: tu (あんた).
  - Truth and Rush: tu (peers; Rush says おまえ). Zora to Yoyo: vous (姫さま). Hornet to Yoyo: vous. Zora's son to
    Byuu: vous.
  - Enemies to one rebel: tu; to the rebels: vous. The King, the Holy Dragons and Bahamut to humans: tu; Yoyo to
    the Holy Dragons: vous. Shops to Byuu: vous; the Patronne: tu.
- タイチョー's joke (0020 0x512, « I'm Taicho, so I'm the captain »). **Decision: keep the circular logic, drop the
  homophone:** « Je suis Taicho, donc je serai capitaine, affirmatif ! » / Matelite: « Taicho sera capitaine ! ».
  隊長 is capitaine; Commandant and Sergent go, Taicho and Gunso are names.
- ドラゴンおやじ. **Decision: Père Dragon.** He raised Salamand as a father and the gag makes him the grandpa;
  « le père » carries both. おかみさん stays Patronne.
- 救世軍 and 解放軍. **Decision: l'Armée du salut d'Orelus for 救世軍 (its JP name is the Salvation Army's),
  l'armée de libération for 解放軍,** the name Matelite turns down for Rebelles (0020 0x226).
- 竜人. **Decision: homme-dragon, hommes-dragons**, not être-dragon or Peuple Dragon.
- 戦場をかける商人 and the other merchants. **Decision: Marchand:** as the label; 妻子を守る商人 is « Marchand père de
  famille: ».
- Quotes. **Decision: ``…''** (codes 86 and 87), not the 「」 glyphs.
- Choice options. **Decision: set two spaces (10 px) in**, by the build (utils/dialog_layout.py OPTION_INDENT).
- Choice prompts. **Decision: the script decides, not [end1].** A text the room script asks with (yes_no 08,
  multiple_choice 09) carries `choice="yes_no"` or `choice="multiple"`; the build reflows its prompt like any text and
  keeps its options, the last lines opening on a space, a line each.
- Centred text. **Decision: the script decides, not leading spaces.** A text the room script shows without a window
  (open_window 0) carries `window="none"` and the build centres each of its lines, as written; `align="left"` or
  `align="center"` on the <text> overrides. Lines carry no leading spaces for centring. `align="steps"` sets each
  line of a block 10 px further in than the one before, the JP's staircase: the 0247 epilogue.
- でアリマス. **Decision: « affirmatif » once a speech at most**, on its last sentence; none in grief, none on a
  question (でアリマスか is the question alone).
- ドラグナー for Yoyo. **Decision: Dragonnière**; Dragonnier stays for the class and the generic « celui qui ».
- スロウランサー. **Decision: Lancer de lancier** (75 px). No slow status exists in the game and the lancers' range
  move is already Javelot; the pun covers throwing the lance and throwing the lancer. Unconfirmed until the
  animation is seen.
- アースウォリアー. **Decision: Guerrier d'argile** (68 px), keeping the ウォリア family (Guerrier blanc, toxique, de
  fer); Golem invents a creature. Guerrier de terre (74 px) if the dragon field is ever shown to hold it.
- おうじょの???. **Decision: ??? de princesse**, beside ??? de Gunso.
- 0045 0xb39, the Uniasticot gift. **Decision: 10**: the script loops give_item ten times; the JP's (1ぴき) undercounts.
- [0xf0][0xf4]げ. **Decision: Munimuni** (record 0x7, as げ is 0x07 in jp.tbl).
- 0012 0x1031 なれるのかな. **Decision: なれる, « redevenir comme avant »**: 〜みたいになれる, not 慣れる.
- 0031 0x278 [F2F0]えとくなよ. **Decision: 鍛えとく, « on va s'endurcir »**, medium confidence: F2F0 is missing from
  jp.tbl and its glyph is blank in text2/ocr.
- アニキ (Bikebake to Byuu). **Decision: Byuu, or nothing; « le grand Byuu » in the third person.** Never
  « grand frère »: Bikebake isn't his brother, and « Byuu, grand frère » reads as a translated honorific.
- Titles in address. **Decision: the title once, then the name, a pronoun or nothing.** ビュウ隊長 called out is
  « Capitaine ! », not « Capitaine Byuu ! »; [ヨヨ]さま spoken to is « princesse » after the first time in a speech;
  神竜ヴァリトラ is « Vritra » once the scene has named it. Jp repeats nouns for want of pronouns; French doesn't.
- ごくろうさま, おつかれさま. **Decision: what the situation says in French**: « Beau travail » for a job done,
  « Tu dois être épuisé » after a journey, « Au rapport » from a guard to his chief, a plain greeting to someone at
  work. Never « tu as bien travaillé » or « merci pour ta peine ».
- ね, ですね. **Decision: no « n'est-ce pas. » with a full stop.** A check is a question (« Vous devez être… »,
  « …, non ? ») or a plain statement.
- A name called out. **Decision: inside the sentence after a comma**: « Pas vrai, Byuu !! », not
  « Pas vrai !! Byuu !! ».
- 〜屋です. **Decision: « Bienvenue au magasin d'armures ! »**, not « Ici le magasin d'armures ! ».
- 奇跡の大陸. **Decision: le continent des miracles**, the chapter title's wording, everywhere.
- フェイズしゅうりょう. **Decision: Fin de phase.** ターン is the turn (Tour), フェイズ half of it; the confirmation
  already says « Fin de la phase du joueur ».

## Spell names

1. **A series is a form and a qualifier**: Onde de feu, Frappe vampire. One JP suffix, one form; no two
   suffixes share a form.
2. **One JP word, one French word**, everywhere it appears: そら ciel, てんくう céleste, いかり colère, えんれつ
   ardent, ナイトメア cauchemar.
3. **Same JP, same French**: the repeated Magie mystère, Vritra, Uhyohyohyo, Fraîcheur are one name.
4. **Nouns**: Soin adverse, not Soigne ennemis; Fraîcheur, not Rafraîchir. A cry or an exclamation stays one
   (Rejoins-nous, Hihihihi).
5. **No name shared with an item**: Sangsue, not Remède.
6. **75 pixels at most** in small_font, Frappe de foudre's width: the skill lists and the combat scene banner fit
   it. `utils/tests/test_name_tables.py` measures every name.
7. **Accents written out**, capitals included (Échec): small_font folds them, the text keeps them.
8. **A set phrase may use a form's word** when it isn't a qualifier after it: Onde de choc, Canon à onde, Coup
   net.

### Forms

| JP | Form | Target |
|---|---|---|
| パルス | Onde | one enemy |
| ブ-ス | Rafale | one enemy |
| タワ- | Tour | all enemies |
| ダスト | Nuée | all enemies |
| ヒット | Frappe | all enemies |
| ブレス | Souffle | |
| ゲイズ | Regard | |
| ゲイル | Orage | |
| スト-ム | Tempête | |
| ウェ-ブ | Vague | |
| パイア | -spiration | one enemy |
| ダンス, おどり | Danse | |

### Families

| JP | Rule | Names |
|---|---|---|
| summons | as their dragon | Vritra, Léviathan, Garuda, Jormungand, Hypérion, Bahamut, Alexandre |
| -ちゃん, -ンチョ | -chou | Vritrachou, Léviachou, Alexchou |
| にんじん | carotte | Carotte, Rayon carotte, Grosse carotte, P'tite carotte |
| みんな | général | Soin général, Dégâts généraux, Croâ général |
| なぞのまほう | | Magie mystère |
