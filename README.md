# rfkc-activity-scheduler

The goal of this project is to help automate scheduling activity blocks for RFKC.

# Details

## Groups

TBD follow up with Mikki

| Gender | Age(s) |
| ------ | ------ |
| Girls | 6 |
| Boys | 6 |

## Activities

TBD follow up with Mikki

| Activity | Distance from breakfast club building (min) | Distance from cafeteria (min) | Distance from chapel (min) | Allowed age group(s) | Required (Y/N) | Notes |
| ------ | ------ | ------ | ------ | ------ | ------ |
| Horses | ? | ? | ? | - | Y |
| Mountain bike riding | 15 | 20 | 25 | - | Y |
| Climbing wall + zipline | ? | ? | ? | only older campers? | Y |
| High ropes course | ? | ? | ? | grads only? | Y |
| Archery | 10 | 15 | 20 | - | Y |
| Arts + crafts + carpentry | 0 | 5 | 10 | Y |
| Free time/drum circle | 0 | 0 | 0 | - | Y | Fill in as needed once other activities are set |


Locations + Activities

```mermaid
flowchart LR    Longhouse --- |"5 min"| FlagPole
    FlagPole --- |"5 min"| DiningHall["Dining Hall / Cafeteria"]
    DiningHall --- |"5 min"| Pool
    Pool --- |"1 min"| Chapel
    
    MountainBiking --- |"15 min"| Longhouse
    RockClimbing --- |"15 min"| Longhouse
    
    FlagPole --- |"10 min"| Horses
    Horses --- |"10 min"| Archery

    HighRopes --- |"0 min"| RockClimbing
    DrumCircle --- |"0 min"| Pool
```

### Requirements

Each activity can have two camper groups at a time, one girls group and one boys group. The groups do not have to be similar in age. 
