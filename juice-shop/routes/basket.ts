/*
 * Copyright (c) 2014-2026 Bjoern Kimminich & the OWASP Juice Shop contributors.
 * SPDX-License-Identifier: MIT
 */

import { type Request, type Response, type NextFunction } from 'express'
import { ProductModel } from '../models/product'
import { BasketModel } from '../models/basket'

import * as utils from '../lib/utils'
import * as security from '../lib/insecurity'

export function retrieveBasket () {
  return async (req: Request, res: Response, next: NextFunction) => {
    try {
      const id = req.params.id
      // FIX V3 (CWE-639, IDOR): a basket may only be retrieved by the user it belongs to.
      // Previously the id from the URL was trusted outright, so any authenticated user could
      // read (and, via the same missing check elsewhere, tamper with) any other user's basket
      // just by changing the id. See remediation/README.md.
      const authenticatedUser = security.authenticatedUsers.from(req)
      if (authenticatedUser == null || String(authenticatedUser.bid) !== String(id)) {
        res.status(403).json({ error: 'Access to this basket is not permitted.' })
        return
      }
      const basket = await BasketModel.findOne({ where: { id }, include: [{ model: ProductModel, paranoid: false, as: 'Products' }] })
      if (((basket?.Products) != null) && basket.Products.length > 0) {
        for (let i = 0; i < basket.Products.length; i++) {
          basket.Products[i].name = req.__(basket.Products[i].name)
        }
      }

      res.json(utils.queryResultToJson(basket))
    } catch (error) {
      next(error)
    }
  }
}
