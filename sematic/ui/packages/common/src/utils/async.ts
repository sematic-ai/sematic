let ID = 0;

interface ReleaseHandle {
    (): void;
}
export class AsyncInvocationQueue {
    private queue: any[] = [];
    private instanceID: number;

    constructor() {
        this.queue = [];
        this.instanceID = ID++;
    }

    async acquire(): Promise<ReleaseHandle> {
        let resolve: any;
        const waitingPromise = new Promise((_resolve) => {
            resolve = _resolve;
        });
        this.queue.push(waitingPromise);

        // Wait until all the promises before this one have been resolved
        while (this.queue.length !== 0) {
            if (this.queue[0] === waitingPromise) {
                break;
            }
            await this.queue.shift();
            // sleep
            await new Promise((resolve) => setTimeout(resolve, 50));
        }

        // The resolve function can be used to release to the next item in the queue
        return resolve;
    }

    get InstanceID() {
        return this.instanceID;
    }

    get IsBusy() {
        return this.queue.length > 0;
    }
}
