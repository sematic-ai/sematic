declare namespace Cypress {
    interface Chainable {
    //   login(email: string, password: string): Chainable<void>
    //   drag(subject: string, options?: Partial<TypeOptions>): Chainable<Element>
    //   dismiss(subject: string, options?: Partial<TypeOptions>): Chainable<Element>
    //   visit(originalFn: CommandOriginalFn, url: string, options: Partial<VisitOptions>): Chainable<Element>
        getBySel(dataTestAttribute: string, args?: any): Chainable<JQuery<HTMLElement>>;
        getBySelLike(dataTestAttribute: string, args?: any): Chainable<JQuery<HTMLElement>>;
    }
}