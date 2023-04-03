/// <reference types="react" />
/// <reference types="cypress" />

declare namespace Cypress {
    type mount = typeof import('cypress/react18').mount;

    interface Chainable {
    //   login(email: string, password: string): Chainable<void>
    //   drag(subject: string, options?: Partial<TypeOptions>): Chainable<Element>
    //   dismiss(subject: string, options?: Partial<TypeOptions>): Chainable<Element>
    //   visit(originalFn: CommandOriginalFn, url: string, options: Partial<VisitOptions>): Chainable<Element>
        matchImage(options?: {
            title?: string,
            maxDiffThreshold?: number,
        }): Chainable<JQuery<HTMLElement>>,
        mount(jsx: React.ReactNode, options?: Parameters<mount>[1], rerenderKey?: string): ReturnType<mount>;
        getBySel(dataTestAttribute: string, args?: any): Chainable<JQuery<HTMLElement>>;
        getBySelLike(dataTestAttribute: string, args?: any): Chainable<JQuery<HTMLElement>>;
    }
}