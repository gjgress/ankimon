# Trade Code


> This trade code defines what pokemon to receive and all the available meta data linked to it. 

When trading with others, **two trade codes** are required for the transfer. 
1. **Your own** Trade Code
2. **The other trainers** trade Code

---

This approach allows modification of the received pokemon if the cheater is familiar with the code mappings.
- When modifying one of the values the pokemons sprite changes. 


## Trade Code Structure

> Each code contains **17 integer values** each separated by a `,`.

<u>*Example*:</u>
- {value}, {value}, {value}, `...`
- 1, 0, 0, 0, 0, 0, 0, 28, 8,  `...`


### Internal Code Handling

>Inside the Class [Pokemon Trade](../pyobj/pokemon_trade.py#trade_pokemon_in) the method `trade_pokemon_in` **stores** the different **integers** from the trade code **in a list.**

```python
# for loop with "," as the delimiter
numbers = [int(num) for num in code.split(',')]
```

Additionally there are **two checks for Invalidity**
1. The Trade Code **contains all** the **necessary values** (length check)
2. **Both pokemon** for trade **are the same **(by pokedex)



## Value Mappings


| index | variableName | description |
| ----- | ------------ | ----------- |

