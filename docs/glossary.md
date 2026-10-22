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

## Game words

Item and class names in the dialog are written as items.xml and classes.xml spell them, in their case, accents
included: Remède, not DROGUE; Dragonnier, not Dragoon; Croisé, not Chevalier Croix; Diablotin, not Petit Démon.

| JP | FR | Not |
|---|---|---|
| ピロー | Piro | GP, Po |
| ターン | Tour | |
| フェイズ | Phase | Tour |
| じょうほう (menu) | Inventaire | Infos |
| そうびしているかず | Équipés (next to Possédés) | NOMBRE EQUIPE |
| セーブ | Sauvegarder | Sauver |
| データがありません | Aucune donnée | PAS DE DONNEES |
| そうびなし | Aucun | NO ITEM |
| したしさ | Affin. | Joie |

## Open

Not decided yet, so neither rule above nor the text settles them:

- パーティー: Équipe in the menus and the battle command, groupe in battle messages.
- クロスナイト (class) and クルーセイダー (dragon) are both Croisé.
- ゴドランド Godrand or Godland; ダフィラ Dafira or Dafila; テード Teid or Tedd; レスタット Restatto or Lestat.
- 反乱軍: Rebelles (17) or Résistance (2).
- The dragon screen's STR, VIT, DEX, MIND, EXP, NEXT: For., Endu., Adr., Esprit, Exp., Suiv. proposed (Vit. is
  already speed).
- Tu or vous between the same two characters: one choice per pair, kept for the whole game.

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
