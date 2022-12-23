import time

class StateMachine():
    def __init__(self, firstState: str):
        self.state: str = firstState
        self.stateChanged: bool = True

    def ms_since(self, start_ms: int) -> int:
        return time.ticks_diff(time.ticks_ms(), start_ms)


    def setState(self, new_state: str):
        self.stateChanged = new_state != self.state
        self.state = new_state
        
        if self.stateChanged:
            print('state is', new_state)

    async def loop(self):
        func = getattr(self, self.state, None)
        if func == None:
            print(f'State {self.state} does not exist')
        else:
            self.setState(func(self.stateChanged))

