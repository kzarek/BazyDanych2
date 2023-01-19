const express = require("express");
const productRoutes = express.Router();
const dbo = require("../db/conn");
const ObjectId = require("mongodb").ObjectId;

productRoutes.get("/products", async(req, res) => {
    const sort_by = req.query.sort;
    let db_connect = await dbo.getDb("mongo");
    db_connect.collection("products").find({}).toArray( async (err, result) => {
        if (err) throw err;
        if (!sort_by) {
            return res.send(result)
        }
        const sorted_result = result.sort((a, b) => a[sort_by] - b[sort_by])
        return res.send(sorted_result)
    })
})

productRoutes.post("/products", async (req, res) => {
    const newProduct = {
        name: req.body.name,
        price: req.body.price,
        description: req.body.description,
        qty: req.body.qty,
        unit: req.body.unit
    }
    
    let db_connect = await dbo.getDb("mongo");
    db_connect.collection("products").findOne({name: new RegExp('^'+newProduct.name+'$', "i")}, function(err, product) {
        if (product) {
            return res.send("You can not add product that already exists")
        }
        db_connect.collection("products").insertOne(newProduct, async(err, result) => {
            if (err) throw err;
            res.send(result)
        })
      });
})


productRoutes.put("/products/:id", async(req, res) => {
    let db_connect = await dbo.getDb("mongo");
    const product_id = {_id: ObjectId(req.params.id)};
    const newValues = {
        $set: {
            name: req.body.name,
            price: req.body.price,
            description: req.body.description,
            qty: req.body.qty,
            unit: req.body.unit
        },
    };
    db_connect.collection("products").updateOne(product_id, newValues, async(err, result) => {
        if (err) throw err;
        res.send(result)
    })
})

productRoutes.delete("/products/:id", async(req, res) => {
    let db_connect = await dbo.getDb("mongo");
    const product_id = {_id: ObjectId(req.params.id)};
    db_connect.collection("products").deleteOne(product_id, async(err, result) => {
        if (err) console.log(err);;
        res.send(result)
    })
})





module.exports = productRoutes;