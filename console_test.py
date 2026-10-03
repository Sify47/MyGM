from core.enums import Gender, Division, ChampionshipTier, MatchStipulation, WinnerMode, StoryBeatType
from domain.models.wrestler import Wrestler
from domain.models.championship import Championship
from core.enums import WrestlerClass, Alignment

# Test 1: Wrestler with gender
male = Wrestler(
    name='Test Male',
    wrestler_class=WrestlerClass.BRAWLER,
    alignment=Alignment.FACE,
    gender=Gender.MALE,
)
female = Wrestler(
    name='Test Female',
    wrestler_class=WrestlerClass.HIGH_FLYER,
    alignment=Alignment.HEEL,
    gender=Gender.FEMALE,
)

print('Male:', male)
print('Female:', female)
print('can_face (M vs F):', male.can_face(female))
print('can_face (M vs M):', male.can_face(male))

# Test 2: Championship
world = Championship(
    name='World Heavyweight Championship',
    division=Division.MEN,
    tier=ChampionshipTier.TOP,
    prestige=70,
)
womens = Championship(
    name="World Women's Championship",
    division=Division.WOMEN,
    tier=ChampionshipTier.TOP,
    prestige=70,
)

print()
print(world)
print(womens)
print('Male can compete in World:', world.can_compete(male))
print('Female can compete in World:', world.can_compete(female))
print("Male can compete in Women's:", womens.can_compete(male))
print("Female can compete in Women's:", womens.can_compete(female))
