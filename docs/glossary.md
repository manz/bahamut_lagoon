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

Still English on the dragon screen (`text/inline.xml`): STR, VIT, DEX, MIND, EXP:, NEXT:, BONUS, NO ITEM.

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
  - Palparos and Sauzer: tu. Palparos to Byuu and to Yoyo: tu; Yoyo to Palparos: tu. Sauzer to Yoyo: vous.
  - Enemies to one rebel: tu; to the rebels: vous. The King, the Holy Dragons and Bahamut to humans: tu; Yoyo to
    the Holy Dragons: vous. Shops to Byuu: vous; the Patronne: tu.
- タイチョー's joke (0020 0x512, « I'm Taicho, so I'm the captain »). **Decision: keep the circular logic, drop the
  homophone:** « Je suis Taicho, donc je serai capitaine, affirmatif ! » / Matelite: « Taicho sera capitaine ! ».
  隊長 is capitaine; Commandant and Sergent go, Taicho and Gunso are names.
- ドラゴンおやじ. **Decision: Père Dragon.** He raised Salamand as a father and the gag makes him the grandpa;
  « le père » carries both. おかみさん stays Patronne.
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
