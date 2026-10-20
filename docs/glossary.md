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
