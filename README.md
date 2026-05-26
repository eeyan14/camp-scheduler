# rfkc-activity-scheduler

At RFKC campers have the opportunity to experience various activities outside of large-group programming. Campers are organized into groups by age and gender, and each of these groups has the opportunity to participate in every offered activity (barring certain age requirements noted below). The goal of this project is to maximize time spent at each activity and minimize the amount of time needed to travel between different activities.

# Outstanding questions

Follow up with Mikki about:
- groups and ages
- activities and locations w/ maps
- are connie and charlie doing meals with groups?

# Details

## Groups

TODO follow up with Mikki

| Gender | Age(s) |
| ------ | ------ |
| Girls | 6 |
| Boys | 6 |

## Activities

TODO follow up with Mikki

| Activity | Distance from breakfast club building (min) | Distance from cafeteria (min) | Distance from chapel (min) | Allowed age group(s) | Required (Y/N) | Notes |
| ------ | ------ | ------ | ------ | ------ | ------ | ------ |
| Horses | ? | ? | ? | - | Y |
| Mountain bike riding | 15 | 20 | 25 | - | Y |
| Climbing wall + zipline | ? | ? | ? | only older campers? | Y |
| High ropes course | ? | ? | ? | grads only? | Y |
| Archery | 10 | 15 | 20 | - | Y |
| Arts + crafts + carpentry | 0 | 5 | 10 | Y |
| Free time/drum circle | 0 | 0 | 0 | - | Y | Fill in as needed once other activities are set |

Free time can be used to fill activity blocks once other activities have been completed; free time can be used for an activity block at any point, not just the end of the week.

TODO photography?

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

Each activity can have two groups at a time, and some can have more (indicated somewhere TODO). Typically it is one girls group and one boys group but can be both girls or both boys if there are not equal numbers. The groups do not have to be similar in age. 

A schedule for the rest of the day, with other programming, will be provided with spaces for activity blocks. If two activity blocks are back-to-back, distance between the two activities should be considered. If a group is meeting Grandma and Grandpa in the cafeteria after an activity, distance should also be considered.